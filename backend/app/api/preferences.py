from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi_csrf_protect import CsrfProtect
from fastapi_csrf_protect.exceptions import CsrfProtectError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_employee
from app.core.csrf import validate_request_origin
from app.core.database import get_db
from app.models.employee import Employee
from app.models.employee_profile import EmployeeProfile
from app.schemas.preferences import (
    EmployeePreferencesResponse,
    UpdateEmployeePreferencesRequest,
)

router = APIRouter(
    prefix="/preferences",
    tags=["Preferences"],
)


@router.get(
    "",
    response_model=EmployeePreferencesResponse,
)
async def get_preferences(
    employee: Annotated[Employee, Depends(get_current_employee)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> EmployeePreferencesResponse:
    profile = await db.scalar(
        select(EmployeeProfile).where(
            EmployeeProfile.user_id == employee.user_id,
        )
    )

    if profile is None:
        return EmployeePreferencesResponse(
            directness="balanced",
            response_length="medium",
            highlight_ambiguity=True,
            step_by_step_guidance=True,
            always_show_next_step=True,
        )

    return EmployeePreferencesResponse.model_validate(profile)


@router.patch(
    "",
    response_model=EmployeePreferencesResponse,
    dependencies=[Depends(validate_request_origin)],
)
async def update_preferences(
    request: Request,
    payload: UpdateEmployeePreferencesRequest,
    employee: Annotated[Employee, Depends(get_current_employee)],
    db: Annotated[AsyncSession, Depends(get_db)],
    csrf_protect: Annotated[CsrfProtect, Depends()],
) -> EmployeePreferencesResponse:
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
            detail="Preferences cannot be null",
        )

    profile = await db.scalar(
        select(EmployeeProfile).where(
            EmployeeProfile.user_id == employee.user_id,
        )
    )

    if profile is None:
        profile = EmployeeProfile(user_id=employee.user_id)
        db.add(profile)

    for field, value in changes.items():
        setattr(profile, field, value)

    await db.commit()
    await db.refresh(profile)

    return EmployeePreferencesResponse.model_validate(profile)
