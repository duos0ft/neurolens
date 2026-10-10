import secrets
from datetime import datetime, timezone
from urllib.parse import urlsplit

from fastapi import HTTPException, Request, status, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.settings import settings
from app.models.employee_session import EmployeeSession
from app.services.oauth import hash_token


def validate_request_origin(request: Request) -> None:
    origin = request.headers.get("origin")

    expected = urlsplit(settings.frontend_url)

    if not origin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Missing Origin header",
        )

    received = urlsplit(origin)

    if (
        received.scheme != expected.scheme
        or received.netloc != expected.netloc
        or received.username is not None
        or received.password is not None
        or received.path not in ("", "/")
        or received.query
        or received.fragment
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid request origin",
        )


async def validate_csrf(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> None:
    validate_request_origin(request)

    session_token = request.cookies.get(settings.session_cookie_name)
    csrf_token = request.headers.get("X-CSRF-Token")

    if not session_token or not csrf_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Missing CSRF token",
        )

    session = await db.scalar(
        select(EmployeeSession).where(
            EmployeeSession.session_hash == hash_token(session_token),
            EmployeeSession.expires_at > datetime.now(timezone.utc),
            EmployeeSession.revoked_at.is_(None),
        )
    )

    if session is None or not session.csrf_token_hash:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid CSRF token",
        )

    expected_hash = session.csrf_token_hash
    received_hash = hash_token(csrf_token)

    if not secrets.compare_digest(expected_hash, received_hash):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid CSRF token",
        )
