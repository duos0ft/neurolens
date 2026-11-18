import uuid
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_factory, get_db
from app.core.settings import settings
from app.models.employee import Employee
from app.models.employee_session import EmployeeSession
from app.services.authentication.oauth import hash_token

SESSION_IDLE_TIMEOUT = timedelta(hours=12)
SESSION_ACTIVITY_INTERVAL = timedelta(minutes=5)
SESSION_ABSOLUTE_LIFETIME = timedelta(days=7)


async def update_session_activity(
    session_id: uuid.UUID,
    now: datetime,
) -> bool:
    idle_cutoff = now - SESSION_IDLE_TIMEOUT
    activity_cutoff = now - SESSION_ACTIVITY_INTERVAL
    absolute_cutoff = now - SESSION_ABSOLUTE_LIFETIME

    async with async_session_factory() as db:
        result = await db.execute(
            update(EmployeeSession)
            .where(
                EmployeeSession.id == session_id,
                EmployeeSession.expires_at > now,
                EmployeeSession.created_at > absolute_cutoff,
                EmployeeSession.last_active_at > idle_cutoff,
                EmployeeSession.last_active_at <= activity_cutoff,
                EmployeeSession.revoked_at.is_(None),
            )
            .values(last_active_at=now)
            .returning(EmployeeSession.id)
        )

        updated = result.scalar_one_or_none() is not None

        await db.commit()

        return updated


async def get_current_employee(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Employee:
    return await authenticate_employee(
        request=request,
        db=db,
        track_activity=True,
    )


async def get_current_employee_read_only(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Employee:
    return await authenticate_employee(
        request=request,
        db=db,
        track_activity=False,
    )


async def authenticate_employee(
    request: Request,
    db: AsyncSession,
    *,
    track_activity: bool,
) -> Employee:
    session_token = request.cookies.get(settings.session_cookie_name)

    if not session_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    now = datetime.now(timezone.utc)

    idle_cutoff = now - SESSION_IDLE_TIMEOUT
    activity_cutoff = now - SESSION_ACTIVITY_INTERVAL
    absolute_cutoff = now - SESSION_ABSOLUTE_LIFETIME

    result = await db.execute(
        select(Employee, EmployeeSession)
        .join(
            EmployeeSession,
            EmployeeSession.employee_id == Employee.user_id,
        )
        .where(
            EmployeeSession.session_hash == hash_token(session_token),
            EmployeeSession.expires_at > now,
            EmployeeSession.created_at > absolute_cutoff,
            EmployeeSession.last_active_at > idle_cutoff,
            EmployeeSession.revoked_at.is_(None),
            Employee.status == "active",
        )
    )

    record = result.one_or_none()

    if record is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session",
        )

    employee, session = record

    if track_activity and session.last_active_at <= activity_cutoff:
        updated = await update_session_activity(
            session.id,
            now,
        )

        if not updated:
            # A concurrent request may have refreshed the session,
            # or the session may have expired or been revoked.
            async with async_session_factory() as check_db:
                valid_session = await check_db.scalar(
                    select(EmployeeSession.id).where(
                        EmployeeSession.id == session.id,
                        EmployeeSession.expires_at > now,
                        EmployeeSession.created_at > absolute_cutoff,
                        EmployeeSession.last_active_at > idle_cutoff,
                        EmployeeSession.revoked_at.is_(None),
                    )
                )

            if valid_session is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired session",
                )

    return employee
