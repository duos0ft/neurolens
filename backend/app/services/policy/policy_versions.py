import io
import logging
import uuid
from datetime import date

from pypdf import PdfReader
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.policy_document import PolicyDocument
from app.models.policy_version import PolicyVersion
from app.services.policy.policy_storage import PolicyStorageService

logger = logging.getLogger(__name__)

MAX_POLICY_FILE_SIZE = 10 * 1024 * 1024


class PolicyDocumentNotFoundError(Exception):
    pass


class InvalidPolicyFileError(Exception):
    pass


class PolicyVersionService:
    def __init__(
        self,
        db: AsyncSession,
        storage: PolicyStorageService | None = None,
    ) -> None:
        self.db = db
        self.storage = storage or PolicyStorageService()

    @staticmethod
    def validate_pdf(
        content: bytes,
    ) -> None:
        if not content:
            raise InvalidPolicyFileError("Policy PDF cannot be empty")

        if len(content) > MAX_POLICY_FILE_SIZE:
            raise InvalidPolicyFileError("Policy PDF cannot exceed 10 MB")

        if not content.startswith(b"%PDF-"):
            raise InvalidPolicyFileError("Uploaded file is not a valid PDF")

        try:
            reader = PdfReader(
                io.BytesIO(content),
                strict=True,
            )

            if reader.is_encrypted:
                raise InvalidPolicyFileError("Encrypted PDFs are not supported")

            if len(reader.pages) == 0:
                raise InvalidPolicyFileError("PDF must contain at least one page")

        except InvalidPolicyFileError:
            raise

        except Exception as error:
            raise InvalidPolicyFileError("Unable to read the uploaded PDF") from error

    async def upload_version(
        self,
        document_id: uuid.UUID,
        employee_id: uuid.UUID,
        filename: str,
        content: bytes,
        effective_date: date | None,
    ) -> PolicyVersion:
        self.validate_pdf(content)

        if not filename or len(filename) > 255:
            raise InvalidPolicyFileError("Invalid PDF filename")

        if not filename.lower().endswith(".pdf"):
            raise InvalidPolicyFileError("Only PDF files are supported")

        version_id = uuid.uuid4()
        uploaded_path: str | None = None
        upload_attempted = False

        try:
            document = await self.db.scalar(
                select(PolicyDocument)
                .where(
                    PolicyDocument.id == document_id,
                )
                .with_for_update()
            )

            if document is None:
                raise PolicyDocumentNotFoundError("Policy document not found")

            latest_version = await self.db.scalar(
                select(func.max(PolicyVersion.version_number)).where(
                    PolicyVersion.document_id == document_id,
                )
            )

            version_number = (latest_version or 0) + 1

            file_path = f"policies/{document_id}/versions/{version_id}.pdf"

            version = PolicyVersion(
                id=version_id,
                document_id=document_id,
                version_number=version_number,
                file_path=file_path,
                original_filename=filename,
                content_type="application/pdf",
                file_size_bytes=len(content),
                effective_date=effective_date,
                ingestion_status="pending",
                publication_status="draft",
                uploaded_by=employee_id,
            )

            self.db.add(version)
            await self.db.flush()

            upload_attempted = True

            uploaded_path = await self.storage.upload_pdf(
                document_id=document_id,
                version_id=version_id,
                content=content,
            )

            if uploaded_path != file_path:
                raise RuntimeError("Unexpected policy storage path")

            await self.db.commit()
            await self.db.refresh(version)

            return version

        except Exception:
            await self.db.rollback()

            if upload_attempted:
                try:
                    await self.storage.delete_pdf(
                        uploaded_path or f"policies/{document_id}/versions/{version_id}.pdf"
                    )
                except Exception:
                    logger.exception("Unable to clean up failed policy upload")

            raise

    async def list_versions(
        self,
        document_id: uuid.UUID,
    ) -> list[PolicyVersion]:
        document = await self.db.get(
            PolicyDocument,
            document_id,
        )

        if document is None:
            raise PolicyDocumentNotFoundError("Policy document not found")

        result = await self.db.scalars(
            select(PolicyVersion)
            .where(
                PolicyVersion.document_id == document_id,
            )
            .order_by(
                PolicyVersion.version_number.desc(),
            )
        )

        return list(result.all())
