from datetime import datetime, timezone
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.settings import settings
from app.models.employee import Employee
from app.models.employee_session import EmployeeSession
from app.services.oauth import hash_token


async def get_current_employee(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Employee:
    session_token = request.cookies.get(settings.session_cookie_name)

    if not session_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    employee = await db.scalar(
        select(Employee)
        .join(
            EmployeeSession,
            EmployeeSession.employee_id == Employee.user_id,
        )
        .where(
            EmployeeSession.session_hash == hash_token(session_token),
            EmployeeSession.expires_at > datetime.now(timezone.utc),
            EmployeeSession.revoked_at.is_(None),
            Employee.status == "active",
        )
    )

    if employee is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session",
        )

    return employee
