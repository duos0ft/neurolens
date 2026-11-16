import uuid
from datetime import date
from typing import Annotated
from urllib.parse import quote

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Request,
    Response,
    UploadFile,
    status,
)
from fastapi_csrf_protect import CsrfProtect
from fastapi_csrf_protect.exceptions import CsrfProtectError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_employee
from app.core.csrf import validate_request_origin
from app.core.database import get_db
from app.core.permissions import require_admin
from app.models.employee import Employee
from app.models.policy_version import PolicyVersion
from app.schemas.policy import (
    CreatePolicyDocumentRequest,
    PolicyDocumentListResponse,
    PolicyDocumentResponse,
    PolicyVersionListResponse,
    PolicyVersionResponse,
)
from app.services.policy_documents import PolicyDocumentService
from app.services.policy_publication import (
    PolicyPublicationConflictError,
    PolicyPublicationNotFoundError,
    PolicyPublicationService,
)
from app.services.policy_storage import (
    PolicyStorageError,
    PolicyStorageNotFoundError,
    PolicyStorageService,
)
from app.services.policy_versions import (
    MAX_POLICY_FILE_SIZE,
    InvalidPolicyFileError,
    PolicyDocumentNotFoundError,
    PolicyVersionService,
)

router = APIRouter(
    prefix="/admin/policies",
    tags=["Company Policies"],
    dependencies=[Depends(require_admin)],
)


@router.get(
    "",
    response_model=PolicyDocumentListResponse,
)
async def list_policy_documents(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PolicyDocumentListResponse:
    documents = await PolicyDocumentService(db).list_documents()

    return PolicyDocumentListResponse(
        documents=[PolicyDocumentResponse.model_validate(document) for document in documents],
    )


@router.post(
    "",
    response_model=PolicyDocumentResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(validate_request_origin)],
)
async def create_policy_document(
    request: Request,
    payload: CreatePolicyDocumentRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    employee: Annotated[Employee, Depends(get_current_employee)],
    csrf_protect: Annotated[CsrfProtect, Depends()],
) -> PolicyDocumentResponse:
    try:
        await csrf_protect.validate_csrf(request)

    except CsrfProtectError as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing CSRF token",
        ) from error

    document = await PolicyDocumentService(db).create_document(
        payload=payload,
        created_by=employee.user_id,
    )

    return PolicyDocumentResponse.model_validate(document)


@router.post(
    "/{document_id}/versions",
    response_model=PolicyVersionResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(validate_request_origin)],
)
async def upload_policy_version(
    document_id: uuid.UUID,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    employee: Annotated[Employee, Depends(get_current_employee)],
    csrf_protect: Annotated[CsrfProtect, Depends()],
    file: Annotated[UploadFile, File()],
    effective_date: Annotated[date | None, Form()] = None,
) -> PolicyVersionResponse:
    try:
        await csrf_protect.validate_csrf(request)

    except CsrfProtectError as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing CSRF token",
        ) from error

    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Only PDF files are supported",
        )

    filename = file.filename or ""

    content = await file.read(MAX_POLICY_FILE_SIZE + 1)
    await file.close()

    if len(content) > MAX_POLICY_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail="Policy PDF cannot exceed 10 MB",
        )

    try:
        version = await PolicyVersionService(db).upload_version(
            document_id=document_id,
            employee_id=employee.user_id,
            filename=filename,
            content=content,
            effective_date=effective_date,
        )

    except PolicyDocumentNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error

    except InvalidPolicyFileError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(error),
        ) from error

    return PolicyVersionResponse.model_validate(version)


@router.get(
    "/{document_id}/versions",
    response_model=PolicyVersionListResponse,
)
async def list_policy_versions(
    document_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PolicyVersionListResponse:
    try:
        versions = await PolicyVersionService(db).list_versions(
            document_id=document_id,
        )

    except PolicyDocumentNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error

    return PolicyVersionListResponse(
        versions=[PolicyVersionResponse.model_validate(version) for version in versions],
    )


@router.get(
    "/{document_id}/versions/{version_id}/file",
)
async def get_policy_version_file(
    document_id: uuid.UUID,
    version_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    download: bool = False,
) -> Response:
    version = await db.scalar(
        select(PolicyVersion).where(
            PolicyVersion.id == version_id,
            PolicyVersion.document_id == document_id,
        )
    )

    if version is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Policy version not found",
        )

    expected_path = f"policies/{document_id}/versions/{version_id}.pdf"

    if version.file_path != expected_path:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Invalid policy file reference",
        )

    try:
        content = await PolicyStorageService().download_pdf(version.file_path)

    except PolicyStorageNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Policy PDF not found",
        ) from error

    except PolicyStorageError as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unable to retrieve policy PDF",
        ) from error

    filename = (
        version.original_filename.replace("\\", "/")
        .split("/")[-1]
        .replace("\r", "")
        .replace("\n", "")
    )

    if not filename.lower().endswith(".pdf"):
        filename = "policy.pdf"

    disposition = "attachment" if download else "inline"

    return Response(
        content=content,
        media_type="application/pdf",
        headers={
            "Content-Disposition": (f"{disposition}; filename*=UTF-8''{quote(filename)}"),
            "Cache-Control": "private, no-store",
            "X-Content-Type-Options": "nosniff",
        },
    )


@router.post(
    "/{document_id}/versions/{version_id}/process",
    response_model=PolicyVersionResponse,
    dependencies=[Depends(validate_request_origin)],
)
async def process_policy_version(
    document_id: uuid.UUID,
    version_id: uuid.UUID,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    csrf_protect: Annotated[CsrfProtect, Depends()],
) -> PolicyVersionResponse:
    try:
        await csrf_protect.validate_csrf(request)
    except CsrfProtectError as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing CSRF token",
        ) from error

    version = await db.scalar(
        select(PolicyVersion).where(
            PolicyVersion.id == version_id,
            PolicyVersion.document_id == document_id,
        )
    )

    if version is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Policy version not found",
        )

    if version.publication_status != "draft":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only draft policy versions can be processed",
        )

    if version.ingestion_status == "processing":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Policy version is already being processed",
        )

    if version.ingestion_status == "ready":
        return PolicyVersionResponse.model_validate(version)

    service = PolicyIngestionService(get_session_factory())

    try:
        await service.process_version(version_id)

    except PolicyVersionNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Policy version not found",
        ) from error

    except PolicyIngestionConflictError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error

    except PolicyIngestionError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to process policy document",
        ) from error

    db.expire_all()

    processed_version = await db.scalar(
        select(PolicyVersion).where(
            PolicyVersion.id == version_id,
            PolicyVersion.document_id == document_id,
        )
    )

    if processed_version is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Policy version not found",
        )

    return PolicyVersionResponse.model_validate(processed_version)


@router.post(
    "/{document_id}/versions/{version_id}/publish",
    response_model=PolicyVersionResponse,
    dependencies=[Depends(validate_request_origin)],
)
async def publish_policy_version(
    document_id: uuid.UUID,
    version_id: uuid.UUID,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    csrf_protect: Annotated[CsrfProtect, Depends()],
) -> PolicyVersionResponse:
    try:
        await csrf_protect.validate_csrf(request)
    except CsrfProtectError as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing CSRF token",
        ) from error

    try:
        version = await PolicyPublicationService(db).publish(
            document_id=document_id,
            version_id=version_id,
        )

    except PolicyPublicationNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error

    except PolicyPublicationConflictError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error

    return PolicyVersionResponse.model_validate(version)
