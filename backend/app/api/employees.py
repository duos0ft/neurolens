from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.pagination import paginate
from app.core.permissions import require_admin
from app.models.employee import Employee
from app.models.employee_profile import EmployeeProfile
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


@router.get("/", response_model=EmployeeListResponse)
async def list_employees(
    db: Annotated[AsyncSession, Depends(get_db)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    search: Annotated[str | None, Query(max_length=100)] = None,
    role: EmployeeRole | None = None,
    status: EmployeeStatus | None = None,
) -> EmployeeListResponse:
    query = select(Employee, EmployeeProfile.display_name).outerjoin(
        EmployeeProfile,
        EmployeeProfile.user_id == Employee.user_id,
    )

    if search and search.strip():
        pattern = f"%{search.strip()}%"

        query = query.where(
            or_(
                Employee.email.ilike(pattern),
                EmployeeProfile.display_name.ilike(pattern),
            )
        )

    if role is not None:
        query = query.where(Employee.role == role.value)

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
            "created_at": row.Employee.created_at,
            "display_name": row.display_name,
        },
    )
