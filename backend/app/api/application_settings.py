from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi_csrf_protect import CsrfProtect
from fastapi_csrf_protect.exceptions import CsrfProtectError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.csrf import validate_request_origin
from app.core.database import get_db
from app.core.permissions import require_admin
from app.models.application_settings import ApplicationSettings
from app.schemas.application_settings import (
    ApplicationSettingsResponse,
    UpdateApplicationSettingsRequest,
)


router = APIRouter(
    prefix="/admin/settings",
    tags=["Application Settings"],
    dependencies=[Depends(require_admin)],
)


@router.get(
    "",
    response_model=ApplicationSettingsResponse,
)
async def get_application_settings(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApplicationSettingsResponse:
    settings = await db.get(ApplicationSettings, 1)

    if settings is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application settings not found",
        )

    return ApplicationSettingsResponse.model_validate(settings)


@router.patch(
    "",
    response_model=ApplicationSettingsResponse,
    dependencies=[Depends(validate_request_origin)],
)
async def update_application_settings(
    request: Request,
    payload: UpdateApplicationSettingsRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    csrf_protect: Annotated[CsrfProtect, Depends()],
) -> ApplicationSettingsResponse:
    try:
        await csrf_protect.validate_csrf(request)

    except CsrfProtectError as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing CSRF token",
        ) from error

    changes = payload.model_dump(exclude_unset=True)

    if any(value is None for value in changes.values()):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Application settings cannot be null",
        )

    if "organization_name" in changes:
        name = changes["organization_name"].strip()

        if not name:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Organization name cannot be empty",
            )

        changes["organization_name"] = name

    settings = await db.get(
        ApplicationSettings,
        1,
        with_for_update=True,
    )

    if settings is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application settings not found",
        )

    for field, value in changes.items():
        setattr(settings, field, value)

    await db.commit()
    await db.refresh(settings)

    return ApplicationSettingsResponse.model_validate(settings)
