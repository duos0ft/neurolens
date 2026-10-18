from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Request,
    status,
)
from fastapi_csrf_protect import CsrfProtect
from fastapi_csrf_protect.exceptions import CsrfProtectError
from sqlalchemy import func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.csrf import validate_request_origin
from app.core.database import get_db
from app.core.pagination import paginate
from app.core.permissions import require_admin
from app.models.employee import Employee
from app.models.employee_invitation import EmployeeInvitation
from app.models.employee_profile import EmployeeProfile
from app.models.employee_session import EmployeeSession
from app.schemas.employee import (
    EmployeeListResponse,
    EmployeeResponse,
    EmployeeRole,
    EmployeeStatus,
)

router = APIRouter(
    prefix="/employees",
    tags=["Employees"],
    dependencies=[Depends(require_admin)],
)


@router.get(
    "/",
    response_model=EmployeeListResponse,
)
async def list_employees(
    db: Annotated[AsyncSession, Depends(get_db)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    search: Annotated[str | None, Query(max_length=100)] = None,
    roles: Annotated[list[EmployeeRole] | None, Query(alias="role")] = None,
    status: EmployeeStatus | None = None,
) -> EmployeeListResponse:
    query = (
        select(
            Employee,
            EmployeeProfile.display_name,
            EmployeeInvitation.status.label("invitation_status"),
        )
        .outerjoin(
            EmployeeProfile,
            EmployeeProfile.user_id == Employee.user_id,
        )
        .outerjoin(
            EmployeeInvitation,
            EmployeeInvitation.employee_id == Employee.user_id,
        )
    )

    if search and search.strip():
        pattern = f"%{search.strip()}%"

        query = query.where(
            or_(
                Employee.email.ilike(pattern),
                EmployeeProfile.display_name.ilike(pattern),
            )
        )

    if roles:
        query = query.where(Employee.role.in_([role.value for role in roles]))

    if status is not None:
        query = query.where(Employee.status == status.value)

    query = query.order_by(
        Employee.created_at.desc(),
        Employee.user_id.desc(),
    )

    return await paginate(
        db,
        query,
        page=page,
        page_size=page_size,
        response_model=EmployeeResponse,
        row_mapper=lambda row: {
            "user_id": row.Employee.user_id,
            "email": row.Employee.email,
            "role": row.Employee.role,
            "status": row.Employee.status,
            "invitation_status": row.invitation_status,
            "created_at": row.Employee.created_at,
            "display_name": row.display_name,
        },
    )


@router.post(
    "/{employee_id}/suspend",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(validate_request_origin)],
)
async def suspend_employee(
    employee_id: UUID,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[Employee, Depends(require_admin)],
    csrf_protect: Annotated[CsrfProtect, Depends()],
) -> None:
    try:
        await csrf_protect.validate_csrf(request)

    except CsrfProtectError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing CSRF token",
        ) from exc

    if employee_id == admin.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot suspend your own account",
        )

    # Serialize administrator availability checks across
    # administrative status-changing operations.
    await db.execute(select(func.pg_advisory_xact_lock(73421)))

    employee = await db.scalar(
        select(Employee)
        .where(
            Employee.user_id == employee_id,
        )
        .with_for_update()
    )

    if employee is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found",
        )

    if employee.status != "active":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only active employees can be suspended",
        )

    if employee.role == "admin":
        active_admin_count = await db.scalar(
            select(func.count())
            .select_from(Employee)
            .where(
                Employee.role == "admin",
                Employee.status == "active",
            )
        )

        if active_admin_count is None or active_admin_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="The last active administrator cannot be suspended",
            )

    now = datetime.now(timezone.utc)

    employee.status = "suspended"

    # Invalidate every existing session belonging
    # to the suspended employee.
    await db.execute(
        update(EmployeeSession)
        .where(
            EmployeeSession.employee_id == employee_id,
            EmployeeSession.revoked_at.is_(None),
        )
        .values(
            revoked_at=now,
        )
    )

    # Persist suspension and session revocations atomically.
    await db.commit()


@router.post(
    "/{employee_id}/reactivate",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(validate_request_origin)],
)
async def reactivate_employee(
    employee_id: UUID,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    csrf_protect: Annotated[CsrfProtect, Depends()],
) -> None:
    try:
        await csrf_protect.validate_csrf(request)

    except CsrfProtectError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing CSRF token",
        ) from exc

    employee = await db.scalar(
        select(Employee).where(Employee.user_id == employee_id).with_for_update()
    )

    if employee is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found",
        )

    if employee.status != "suspended":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only suspended employees can be reactivated",
        )

    if employee.provisioning_status != "completed" or not employee.auth0_user_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Employee identity is not fully provisioned",
        )

    employee.status = "active"

    await db.commit()
