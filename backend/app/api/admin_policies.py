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
    AdminPolicyDocumentListResponse,
    AdminPolicyDocumentResponse,
    CreatePolicyDocumentRequest,
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
    response_model=AdminPolicyDocumentListResponse,
)
async def list_policy_documents(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AdminPolicyDocumentListResponse:
    documents = await PolicyDocumentService(db).list_documents()

    if not documents:
        return AdminPolicyDocumentListResponse(documents=[])

    document_ids = [document.id for document in documents]

    versions = (
        await db.scalars(
            select(PolicyVersion)
            .where(
                PolicyVersion.document_id.in_(document_ids),
            )
            .order_by(
                PolicyVersion.document_id,
                PolicyVersion.version_number.desc(),
            )
        )
    ).all()

    latest_versions: dict[uuid.UUID, PolicyVersion] = {}

    for version in versions:
        latest_versions.setdefault(
            version.document_id,
            version,
        )

    results: list[AdminPolicyDocumentResponse] = []

    for document in documents:
        version = latest_versions.get(document.id)

        if version is None:
            policy_status = "no_document"
        elif version.publication_status != "draft":
            policy_status = version.publication_status
        else:
            policy_status = version.ingestion_status

        results.append(
            AdminPolicyDocumentResponse(
                **PolicyDocumentResponse.model_validate(document).model_dump(),
                latest_version_number=(version.version_number if version is not None else None),
                status=policy_status,
            )
        )

    return AdminPolicyDocumentListResponse(
        documents=results,
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
