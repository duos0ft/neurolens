from typing import Annotated
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_employee_read_only
from app.core.database import get_db
from app.models.employee import Employee
from app.schemas.policy import PublishedPolicyListResponse
from app.services.policy_storage import (
    PolicyStorageError,
    PolicyStorageNotFoundError,
    PolicyStorageService,
)
from app.services.published_policies import PublishedPolicyNotFoundError, PublishedPolicyService

router = APIRouter(
    prefix="/policies",
    tags=["Company Policies"],
)


@router.get(
    "",
    response_model=PublishedPolicyListResponse,
)
async def list_published_policies(
    employee: Annotated[
        Employee,
        Depends(get_current_employee_read_only),
    ],
    db: Annotated[AsyncSession, Depends(get_db)],
    response: Response,
) -> PublishedPolicyListResponse:
    response.headers["Cache-Control"] = "private, no-store"

    documents = await PublishedPolicyService(db).list_policies()

    return PublishedPolicyListResponse(
        documents=documents,
    )


@router.get("/{document_id}/file")
async def get_published_policy_file(
    document_id: uuid.UUID,
    employee: Annotated[
        Employee,
        Depends(get_current_employee_read_only),
    ],
    db: Annotated[AsyncSession, Depends(get_db)],
    download: bool = False,
) -> Response:
    try:
        version = await PublishedPolicyService(db).get_published_version(document_id)

    except PublishedPolicyNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Published policy not found",
        ) from error

    expected_path = f"policies/{document_id}/versions/{version.id}.pdf"

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
