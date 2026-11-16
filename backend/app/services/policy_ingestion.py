import asyncio
import logging

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.ai.capabilities.embeddings import EmbeddingError
from app.ai.providers.embedding_factory import create_embedding_provider
from app.services.policy_chunking import PolicyChunkingService
from app.services.policy_ingestion_jobs import (
    ClaimedPolicyIngestionJob,
    PolicyIngestionJobService,
)
from app.services.policy_storage import (
    PolicyStorageError,
    PolicyStorageService,
)
from app.services.policy_text_extraction import (
    PolicyTextExtractionError,
    PolicyTextExtractionService,
)

logger = logging.getLogger(__name__)

PROCESSING_TIMEOUT_SECONDS = 480


class PolicyIngestionService:
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        self.session_factory = session_factory
        self.storage = PolicyStorageService()
        self.extractor = PolicyTextExtractionService()
        self.chunker = PolicyChunkingService()

    async def process_next(self) -> bool:
        async with self.session_factory() as db:
            job = await PolicyIngestionJobService(db).claim_next()

        if job is None:
            return False

        await self._process_job(job)

        return True

    async def _process_content(
        self,
        job: ClaimedPolicyIngestionJob,
    ) -> tuple:
        content = await self.storage.download_pdf(job.file_path)

        pages = await asyncio.to_thread(
            self.extractor.extract,
            content,
        )

        chunks = await asyncio.to_thread(
            self.chunker.chunk,
            pages,
        )

        if not chunks:
            raise PolicyTextExtractionError("No searchable content was extracted")

        provider = create_embedding_provider()

        embeddings = await provider.embed([chunk.content for chunk in chunks])

        return chunks, embeddings

    async def _complete_success(
        self,
        job: ClaimedPolicyIngestionJob,
        chunks,
        embeddings: list[list[float]],
    ) -> bool:
        async with self.session_factory() as db:
            return await PolicyIngestionJobService(db).complete_success(
                job=job,
                chunks=chunks,
                embeddings=embeddings,
            )

    async def _complete_failure(
        self,
        job: ClaimedPolicyIngestionJob,
        error_code: str,
        retryable: bool,
    ) -> None:
        async with self.session_factory() as db:
            recorded = await PolicyIngestionJobService(db).complete_failure(
                job=job,
                error_code=error_code,
                retryable=retryable,
            )

        if not recorded:
            logger.warning(
                "Policy ingestion attempt no longer owns version %s",
                job.version_id,
            )

    async def _process_job(
        self,
        job: ClaimedPolicyIngestionJob,
    ) -> None:
        try:
            async with asyncio.timeout(PROCESSING_TIMEOUT_SECONDS):
                chunks, embeddings = await self._process_content(job)

                completed = await self._complete_success(
                    job,
                    chunks,
                    embeddings,
                )

            if completed:
                logger.info(
                    "Policy version %s ingested with %d chunks",
                    job.version_id,
                    len(chunks),
                )
            else:
                logger.warning(
                    "Policy ingestion attempt expired for version %s",
                    job.version_id,
                )

        except TimeoutError:
            await self._complete_failure(
                job,
                error_code="processing_error",
                retryable=True,
            )

        except PolicyStorageError:
            await self._complete_failure(
                job,
                error_code="storage_error",
                retryable=True,
            )

        except PolicyTextExtractionError:
            await self._complete_failure(
                job,
                error_code="extraction_error",
                retryable=False,
            )

        except EmbeddingError:
            await self._complete_failure(
                job,
                error_code="embedding_error",
                retryable=True,
            )

        except ValueError:
            await self._complete_failure(
                job,
                error_code="invalid_embedding",
                retryable=False,
            )

        except asyncio.CancelledError:
            raise

        except Exception:
            logger.exception(
                "Unexpected ingestion failure for policy version %s",
                job.version_id,
            )

            await self._complete_failure(
                job,
                error_code="processing_error",
                retryable=True,
            )
