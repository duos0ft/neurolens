import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy import and_, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.policy_chunk import PolicyChunk
from app.models.policy_version import PolicyVersion
from app.services.policy.policy_chunking import ExtractedPolicyChunk

PROCESSING_LEASE_SECONDS = 600
MAX_INGESTION_ATTEMPTS = 5
INITIAL_RETRY_DELAY_SECONDS = 30
MAX_RETRY_DELAY_SECONDS = 1800


@dataclass(frozen=True)
class ClaimedPolicyIngestionJob:
    version_id: uuid.UUID
    attempt_id: uuid.UUID
    file_path: str
    attempt_count: int


class PolicyIngestionJobService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def claim_next(
        self,
    ) -> ClaimedPolicyIngestionJob | None:
        now = datetime.now(timezone.utc)

        try:
            version = await self.db.scalar(
                select(PolicyVersion)
                .where(
                    PolicyVersion.publication_status == "draft",
                    PolicyVersion.ingestion_attempt_count < MAX_INGESTION_ATTEMPTS,
                    or_(
                        and_(
                            PolicyVersion.ingestion_status == "pending",
                            or_(
                                PolicyVersion.next_ingestion_retry_at.is_(None),
                                PolicyVersion.next_ingestion_retry_at <= now,
                            ),
                        ),
                        and_(
                            PolicyVersion.ingestion_status == "failed",
                            PolicyVersion.next_ingestion_retry_at.is_not(None),
                            PolicyVersion.next_ingestion_retry_at <= now,
                        ),
                        and_(
                            PolicyVersion.ingestion_status == "processing",
                            PolicyVersion.processing_lease_expires_at <= now,
                        ),
                    ),
                )
                .order_by(
                    PolicyVersion.created_at,
                    PolicyVersion.id,
                )
                .limit(1)
                .with_for_update(skip_locked=True)
            )

            if version is None:
                await self.db.rollback()
                return None

            attempt_id = uuid.uuid4()

            version.ingestion_status = "processing"
            version.processing_attempt_id = attempt_id
            version.processing_lease_expires_at = now + timedelta(seconds=PROCESSING_LEASE_SECONDS)
            version.ingestion_attempt_count += 1
            version.next_ingestion_retry_at = None
            version.ingestion_error_code = None

            await self.db.execute(
                update(PolicyVersion)
                .where(
                    PolicyVersion.ingestion_status == "processing",
                    PolicyVersion.processing_lease_expires_at <= now,
                    PolicyVersion.ingestion_attempt_count >= MAX_INGESTION_ATTEMPTS,
                )
                .values(
                    ingestion_status="failed",
                    ingestion_error_code="processing_error",
                    processing_attempt_id=None,
                    processing_lease_expires_at=None,
                    next_ingestion_retry_at=None,
                )
            )

            job = ClaimedPolicyIngestionJob(
                version_id=version.id,
                attempt_id=attempt_id,
                file_path=version.file_path,
                attempt_count=version.ingestion_attempt_count,
            )

            await self.db.commit()

            return job

        except Exception:
            await self.db.rollback()
            raise

    async def _get_owned_version(
        self,
        job: ClaimedPolicyIngestionJob,
    ) -> PolicyVersion | None:
        return await self.db.scalar(
            select(PolicyVersion)
            .where(
                PolicyVersion.id == job.version_id,
                PolicyVersion.publication_status == "draft",
                PolicyVersion.ingestion_status == "processing",
                PolicyVersion.processing_attempt_id == job.attempt_id,
                PolicyVersion.processing_lease_expires_at > datetime.now(timezone.utc),
            )
            .with_for_update()
        )

    @staticmethod
    def _release(
        version: PolicyVersion,
    ) -> None:
        version.processing_attempt_id = None
        version.processing_lease_expires_at = None

    async def renew_lease(
        self,
        job: ClaimedPolicyIngestionJob,
    ) -> bool:
        try:
            version = await self._get_owned_version(job)

            if version is None:
                await self.db.rollback()
                return False

            version.processing_lease_expires_at = datetime.now(timezone.utc) + timedelta(
                seconds=PROCESSING_LEASE_SECONDS
            )

            await self.db.commit()
            return True

        except Exception:
            await self.db.rollback()
            raise

    async def complete_success(
        self,
        job: ClaimedPolicyIngestionJob,
        chunks: list[ExtractedPolicyChunk],
        embeddings: list[list[float]],
    ) -> bool:
        if not chunks or len(chunks) != len(embeddings):
            raise ValueError("Policy chunks and embeddings must be nonempty and aligned")

        if any(len(vector) != 1536 for vector in embeddings):
            raise ValueError("Invalid policy embedding dimensions")

        try:
            version = await self._get_owned_version(job)

            if version is None:
                await self.db.rollback()
                return False

            await self.db.execute(
                PolicyChunk.__table__.delete().where(
                    PolicyChunk.version_id == job.version_id,
                )
            )

            self.db.add_all(
                [
                    PolicyChunk(
                        version_id=job.version_id,
                        chunk_index=chunk.chunk_index,
                        content=chunk.content,
                        section_title=chunk.section_title,
                        page_number=chunk.page_number,
                        token_count=chunk.token_count,
                        embedding=embedding,
                    )
                    for chunk, embedding in zip(
                        chunks,
                        embeddings,
                        strict=True,
                    )
                ]
            )

            await self.db.flush()

            version.ingestion_status = "ready"
            version.ingestion_error_code = None
            version.next_ingestion_retry_at = None

            self._release(version)

            await self.db.commit()
            return True

        except Exception:
            await self.db.rollback()
            raise

    async def complete_failure(
        self,
        job: ClaimedPolicyIngestionJob,
        error_code: str,
        retryable: bool,
    ) -> bool:
        allowed_error_codes = {
            "storage_error",
            "extraction_error",
            "embedding_error",
            "invalid_document",
            "invalid_embedding",
            "processing_error",
        }

        if error_code not in allowed_error_codes:
            raise ValueError("Unsupported ingestion error code")

        try:
            version = await self._get_owned_version(job)

            if version is None:
                await self.db.rollback()
                return False

            version.ingestion_status = "failed"
            version.ingestion_error_code = error_code

            self._release(version)

            if retryable and version.ingestion_attempt_count < MAX_INGESTION_ATTEMPTS:
                delay = min(
                    INITIAL_RETRY_DELAY_SECONDS * (2 ** (version.ingestion_attempt_count - 1)),
                    MAX_RETRY_DELAY_SECONDS,
                )

                version.next_ingestion_retry_at = datetime.now(timezone.utc) + timedelta(
                    seconds=delay
                )
            else:
                version.next_ingestion_retry_at = None

            await self.db.commit()
            return True

        except Exception:
            await self.db.rollback()
            raise
