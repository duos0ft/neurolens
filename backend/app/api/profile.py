from typing import Annotated
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

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
from app.schemas.employee.employee import (
    AuthenticatedEmployeeResponse,
    UpdateEmployeeProfileRequest,
)

router = APIRouter(
    prefix="/profile",
    tags=["Profile"],
    dependencies=[Depends(validate_request_origin)],
)


@router.patch(
    "",
    response_model=AuthenticatedEmployeeResponse,
)
async def update_profile(
    request: Request,
    payload: UpdateEmployeeProfileRequest,
    employee: Annotated[Employee, Depends(get_current_employee)],
    db: Annotated[AsyncSession, Depends(get_db)],
    csrf_protect: Annotated[CsrfProtect, Depends()],
) -> AuthenticatedEmployeeResponse:
    try:
        await csrf_protect.validate_csrf(request)

    except CsrfProtectError as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing CSRF token",
        ) from error

    changes = payload.model_dump(exclude_unset=True)

    for field, value in changes.items():
        if isinstance(value, str):
            value = value.strip() or None

        if field == "timezone":
            if value is None:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                    detail="Timezone cannot be empty",
                )

            try:
                ZoneInfo(value)
            except ZoneInfoNotFoundError as error:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                    detail="Invalid timezone",
                ) from error

        changes[field] = value

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

    return AuthenticatedEmployeeResponse(
        id=employee.user_id,
        email=employee.email,
        role=employee.role,
        status=employee.status,
        display_name=profile.display_name,
        job_title=profile.job_title,
        department=profile.department,
        team=profile.team,
    )
