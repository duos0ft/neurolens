import uuid
from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ApplicationSettings
from app.models.policy_document import PolicyDocument
from app.models.policy_version import PolicyVersion
from app.schemas.policy.policy import PublishedPolicyResponse


class PublishedPolicyNotFoundError(Exception):
    pass


class PublishedPolicyService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_policies(self) -> list[PublishedPolicyResponse]:
        result = await self.db.execute(
            select(PolicyDocument, PolicyVersion)
            .join(
                PolicyVersion,
                PolicyVersion.document_id == PolicyDocument.id,
            )
            .where(
                PolicyVersion.publication_status == "published",
                PolicyVersion.ingestion_status == "ready",
                (
                    (PolicyVersion.effective_date.is_(None))
                    | (PolicyVersion.effective_date <= date.today())
                ),
            )
            .order_by(
                PolicyDocument.title.asc(),
                PolicyDocument.id.asc(),
            )
        )

        return [
            PublishedPolicyResponse(
                id=document.id,
                title=document.title,
                description=document.description,
                category=document.category,
                version_id=version.id,
                version_number=version.version_number,
                effective_date=version.effective_date,
                published_at=version.published_at,
            )
            for document, version in result.all()
        ]

    async def get_published_version(
        self,
        document_id: uuid.UUID,
    ) -> PolicyVersion:
        application_settings = await self.db.get(
            ApplicationSettings,
            1,
        )

        organization_timezone = (
            application_settings.default_timezone if application_settings is not None else "UTC"
        )

        current_date = datetime.now(timezone.utc).astimezone(ZoneInfo(organization_timezone)).date()

        version = await self.db.scalar(
            select(PolicyVersion).where(
                PolicyVersion.document_id == document_id,
                PolicyVersion.publication_status == "published",
                PolicyVersion.ingestion_status == "ready",
                (
                    PolicyVersion.effective_date.is_(None)
                    | (PolicyVersion.effective_date <= current_date)
                ),
            )
        )

        if version is None:
            raise PublishedPolicyNotFoundError("Published policy not found")

        return version
