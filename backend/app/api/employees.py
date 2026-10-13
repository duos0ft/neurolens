from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.permissions import require_admin
from app.models.employee import Employee
from app.schemas.employee import EmployeeListResponse

router = APIRouter(
    prefix="/employees",
    tags=["Employees"],
    dependencies=[Depends(require_admin)],
)


@router.get("/", response_model=EmployeeListResponse)
async def list_employees(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> EmployeeListResponse:
    result = await db.execute(select(Employee).order_by(Employee.created_at.desc()))

    return EmployeeListResponse(
        employees=result.scalars().all(),
    )
