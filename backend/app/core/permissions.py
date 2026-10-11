from typing import Annotated

from fastapi import Depends, HTTPException, status

from app.core.auth import get_current_employee
from app.models.employee import Employee


CurrentEmployee = Annotated[
    Employee,
    Depends(get_current_employee),
]


async def require_admin(
    employee: CurrentEmployee,
) -> Employee:
    if employee.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator access required",
        )

    return employee
