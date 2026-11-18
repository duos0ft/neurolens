import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.policy_document import PolicyDocument
from app.models.policy_version import PolicyVersion


class PolicyPublicationNotFoundError(Exception):
    pass


class PolicyPublicationConflictError(Exception):
    pass


class PolicyPublicationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def publish(
        self,
        document_id: uuid.UUID,
        version_id: uuid.UUID,
    ) -> PolicyVersion:
        document = await self.db.scalar(
            select(PolicyDocument).where(PolicyDocument.id == document_id).with_for_update()
        )

        if document is None:
            raise PolicyPublicationNotFoundError("Policy document not found")

        version = await self.db.scalar(
            select(PolicyVersion)
            .where(
                PolicyVersion.id == version_id,
                PolicyVersion.document_id == document_id,
            )
            .with_for_update()
        )

        if version is None:
            raise PolicyPublicationNotFoundError("Policy version not found")

        if version.publication_status == "published":
            return version

        if version.publication_status != "draft":
            raise PolicyPublicationConflictError("Only draft policy versions can be published")

        if version.ingestion_status != "ready":
            raise PolicyPublicationConflictError(
                "Policy version must finish processing before publication"
            )

        now = datetime.now(timezone.utc)

        current_published_version = await self.db.scalar(
            select(PolicyVersion)
            .where(
                PolicyVersion.document_id == document_id,
                PolicyVersion.publication_status == "published",
            )
            .with_for_update()
        )

        if current_published_version is not None:
            current_published_version.publication_status = "archived"
            current_published_version.archived_at = now

            await self.db.flush()

        version.publication_status = "published"
        version.published_at = now
        version.archived_at = None

        await self.db.commit()
        await self.db.refresh(version)

        return version
