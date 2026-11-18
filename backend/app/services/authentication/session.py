import secrets
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings import settings
from app.models.employee_session import EmployeeSession
from app.services.authentication.oauth import hash_token


async def create_employee_session(
    db: AsyncSession,
    employee_id: uuid.UUID,
) -> str:
    session_token = secrets.token_urlsafe(32)

    expires_at = datetime.now(timezone.utc) + timedelta(
        seconds=settings.session_lifetime_seconds,
    )

    session = EmployeeSession(
        employee_id=employee_id,
        session_hash=hash_token(session_token),
        expires_at=expires_at,
    )

    db.add(session)
    await db.flush()

    return session_token
