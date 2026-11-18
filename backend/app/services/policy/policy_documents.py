import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.policy_document import PolicyDocument
from app.schemas.policy.policy import CreatePolicyDocumentRequest


class PolicyDocumentService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_documents(self) -> list[PolicyDocument]:
        result = await self.db.scalars(
            select(PolicyDocument).order_by(
                PolicyDocument.created_at.desc(),
                PolicyDocument.id.desc(),
            )
        )

        return list(result.all())

    async def create_document(
        self,
        payload: CreatePolicyDocumentRequest,
        created_by: uuid.UUID,
    ) -> PolicyDocument:
        try:
            document = PolicyDocument(
                title=payload.title,
                description=payload.description,
                category=payload.category,
                created_by=created_by,
            )

            self.db.add(document)

            await self.db.commit()
            await self.db.refresh(document)

            return document

        except Exception:
            await self.db.rollback()
            raise
