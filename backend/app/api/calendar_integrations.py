import hmac
import logging
from datetime import datetime, timedelta, timezone
from typing import Annotated
from urllib.parse import urlencode
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from fastapi_csrf_protect import CsrfProtect
from fastapi_csrf_protect.exceptions import CsrfProtectError
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import RedirectResponse

from app.core.auth import get_current_employee, get_current_employee_read_only
from app.core.csrf import validate_request_origin
from app.core.database import get_db
from app.core.settings import settings
from app.models.calendar_event import CalendarEvent
from app.models.calendar_integration import CalendarIntegration
from app.models.calendar_oauth_flow import CalendarOAuthFlow
from app.models.calendar_sync_record import CalendarSyncRecord
from app.models.employee import Employee
from app.models.employee_session import EmployeeSession
from app.models.task import Task
from app.services.authentication.oauth import (
    generate_code_challenge,
    generate_token,
    hash_token,
)
from app.services.calendar.calendar_sync import CalendarSyncService
from app.services.calendar.calendar_token_encryption import (
    CalendarTokenEncryption,
    CalendarTokenEncryptionError,
)

router = APIRouter(
    prefix="/integrations/google-calendar",
    tags=["Calendar Integrations"],
)

logger = logging.getLogger(__name__)

GOOGLE_AUTHORIZATION_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_OAUTH_COOKIE_NAME = "neurolens_google_calendar_oauth"
GOOGLE_OAUTH_COOKIE_PATH = "/api/integrations/google-calendar"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"
GOOGLE_REVOCATION_URL = "https://oauth2.googleapis.com/revoke"


class CalendarAuthorizationResponse(BaseModel):
    authorization_url: str


class CalendarIntegrationStatusResponse(BaseModel):
    provider: str
    connected: bool
    integration_id: UUID | None = None
    account_email: str | None = None
    connected_at: datetime | None = None
    last_synced_at: datetime | None = None
    pending_count: int = 0
    syncing_count: int = 0
    failed_count: int = 0


class CalendarDisconnectResponse(BaseModel):
    provider: str
    disconnected: bool


class CalendarSyncRequestResponse(BaseModel):
    queued: bool
    task_count: int
    event_count: int
    deletion_count: int


@router.post(
    "/connect",
    response_model=CalendarAuthorizationResponse,
    dependencies=[Depends(validate_request_origin)],
)
async def connect_google_calendar(
    request: Request,
    employee: Annotated[Employee, Depends(get_current_employee)],
    db: Annotated[AsyncSession, Depends(get_db)],
    csrf_protect: Annotated[CsrfProtect, Depends()],
) -> JSONResponse:
    try:
        await csrf_protect.validate_csrf(request)
    except CsrfProtectError as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing CSRF token",
        ) from error

    if (
        not settings.google_calendar_client_id
        or not settings.google_calendar_client_secret
        or not settings.google_calendar_token_encryption_key
    ):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google Calendar integration is not configured",
        )

    session_token = request.cookies.get(settings.session_cookie_name)

    if not session_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="An active employee session is required",
        )

    state = generate_token()
    browser_nonce = generate_token()
    code_verifier = generate_token()

    scopes = [
        "openid",
        "email",
        settings.google_calendar_scopes,
    ]

    parameters = {
        "client_id": settings.google_calendar_client_id,
        "redirect_uri": settings.google_calendar_redirect_uri,
        "response_type": "code",
        "scope": " ".join(scopes),
        "state": state,
        "code_challenge": generate_code_challenge(code_verifier),
        "code_challenge_method": "S256",
        "access_type": "offline",
        "prompt": "consent",
    }

    authorization_url = f"{GOOGLE_AUTHORIZATION_URL}?{urlencode(parameters)}"

    db.add(
        CalendarOAuthFlow(
            employee_id=employee.user_id,
            provider="google",
            state_hash=hash_token(state),
            browser_nonce_hash=hash_token(browser_nonce),
            session_hash=hash_token(session_token),
            code_verifier=code_verifier,
            expires_at=(
                datetime.now(timezone.utc)
                + timedelta(seconds=settings.oauth_state_lifetime_seconds)
            ),
        )
    )

    await db.commit()

    response = JSONResponse(
        content={
            "authorization_url": authorization_url,
        }
    )

    response.set_cookie(
        key=GOOGLE_OAUTH_COOKIE_NAME,
        value=browser_nonce,
        max_age=settings.oauth_state_lifetime_seconds,
        httponly=True,
        secure=settings.session_cookie_secure,
        samesite="lax",
        path=GOOGLE_OAUTH_COOKIE_PATH,
    )

    response.headers["Cache-Control"] = "no-store"

    return response


def google_connection_redirect(result: str) -> RedirectResponse:
    response = RedirectResponse(
        url=f"{settings.frontend_url}/app/profile?google={result}",
        status_code=status.HTTP_303_SEE_OTHER,
    )

    response.delete_cookie(
        key=GOOGLE_OAUTH_COOKIE_NAME,
        path=GOOGLE_OAUTH_COOKIE_PATH,
    )

    response.headers["Cache-Control"] = "no-store"

    return response


async def consume_google_calendar_flow(
    db: AsyncSession,
    state: str,
    browser_nonce: str,
    session_token: str,
) -> CalendarOAuthFlow | None:
    now = datetime.now(timezone.utc)

    flow = await db.scalar(
        select(CalendarOAuthFlow)
        .where(
            CalendarOAuthFlow.state_hash == hash_token(state),
            CalendarOAuthFlow.provider == "google",
        )
        .with_for_update()
    )

    if flow is None:
        await db.rollback()
        return None

    valid_browser = hmac.compare_digest(
        flow.browser_nonce_hash,
        hash_token(browser_nonce),
    )

    valid_session = hmac.compare_digest(
        flow.session_hash,
        hash_token(session_token),
    )

    valid_flow = (
        valid_browser and valid_session and flow.expires_at > now and flow.consumed_at is None
    )

    if not valid_flow:
        await db.rollback()
        return None

    session = await db.scalar(
        select(EmployeeSession).where(
            EmployeeSession.session_hash == hash_token(session_token),
            EmployeeSession.employee_id == flow.employee_id,
            EmployeeSession.revoked_at.is_(None),
            EmployeeSession.expires_at > now,
        )
    )

    employee = await db.scalar(
        select(Employee).where(
            Employee.user_id == flow.employee_id,
            Employee.status == "active",
        )
    )

    if session is None or employee is None:
        await db.rollback()
        return None

    flow.consumed_at = now

    await db.commit()

    return flow


async def exchange_google_authorization_code(
    code: str,
    code_verifier: str,
) -> dict:
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "client_id": settings.google_calendar_client_id,
                "client_secret": settings.google_calendar_client_secret,
                "code": code,
                "code_verifier": code_verifier,
                "grant_type": "authorization_code",
                "redirect_uri": settings.google_calendar_redirect_uri,
            },
        )

        response.raise_for_status()

        result = response.json()

    if not isinstance(result, dict):
        raise ValueError("Invalid Google token response")

    access_token = result.get("access_token")

    if not isinstance(access_token, str) or not access_token:
        raise ValueError("Google did not provide an access token")

    return result


async def get_google_account(
    access_token: str,
) -> tuple[str, str | None]:
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(
            GOOGLE_USERINFO_URL,
            headers={
                "Authorization": f"Bearer {access_token}",
            },
        )

        response.raise_for_status()

        result = response.json()

    if not isinstance(result, dict):
        raise ValueError("Invalid Google account response")

    account_id = result.get("sub")
    email = result.get("email")

    if not isinstance(account_id, str) or not account_id:
        raise ValueError("Google account identifier is missing")

    if email is not None and not isinstance(email, str):
        email = None

    if email is not None and result.get("email_verified") is not True:
        email = None

    return account_id, email


async def save_google_calendar_connection(
    db: AsyncSession,
    employee_id,
    account_id: str,
    email: str | None,
    refresh_token: str | None,
    scopes: str,
) -> bool:
    connection = await db.scalar(
        select(CalendarIntegration)
        .where(
            CalendarIntegration.employee_id == employee_id,
            CalendarIntegration.provider == "google",
        )
        .with_for_update()
    )

    if connection is not None:
        if connection.provider_account_id != account_id:
            await db.rollback()
            return False

        if refresh_token:
            encryption = CalendarTokenEncryption()
            connection.encrypted_refresh_token = encryption.encrypt(refresh_token)

        connection.account_email = email
        connection.scopes = scopes

    else:
        if not refresh_token:
            await db.rollback()
            return False

        encryption = CalendarTokenEncryption()

        connection = CalendarIntegration(
            employee_id=employee_id,
            provider="google",
            provider_account_id=account_id,
            account_email=email,
            encrypted_refresh_token=encryption.encrypt(refresh_token),
            scopes=scopes,
        )

        db.add(connection)

    await db.commit()

    return True


@router.get("/callback")
async def google_calendar_callback(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RedirectResponse:
    state = request.query_params.get("state")
    code = request.query_params.get("code")

    browser_nonce = request.cookies.get(GOOGLE_OAUTH_COOKIE_NAME)

    session_token = request.cookies.get(settings.session_cookie_name)

    if not state or not browser_nonce or not session_token:
        return google_connection_redirect("invalid_state")

    flow = await consume_google_calendar_flow(
        db=db,
        state=state,
        browser_nonce=browser_nonce,
        session_token=session_token,
    )

    if flow is None:
        return google_connection_redirect("invalid_state")

    if request.query_params.get("error"):
        return google_connection_redirect("cancelled")

    if not code:
        return google_connection_redirect("missing_code")

    if (
        not settings.google_calendar_client_id
        or not settings.google_calendar_client_secret
        or not settings.google_calendar_token_encryption_key
    ):
        return google_connection_redirect("not_configured")

    try:
        token = await exchange_google_authorization_code(
            code=code,
            code_verifier=flow.code_verifier,
        )

        access_token = token["access_token"]

        account_id, email = await get_google_account(access_token)

        granted_scopes = token.get("scope", "")

        if not isinstance(granted_scopes, str):
            raise ValueError("Invalid Google granted scopes")

        granted_scope_set = set(granted_scopes.split())

        required_scopes = {
            settings.google_calendar_scopes,
        }

        if not required_scopes.issubset(granted_scope_set):
            return google_connection_redirect("insufficient_permissions")

        refresh_token = token.get("refresh_token")

        if refresh_token is not None and (not isinstance(refresh_token, str) or not refresh_token):
            raise ValueError("Invalid Google refresh token")

        connected = await save_google_calendar_connection(
            db=db,
            employee_id=flow.employee_id,
            account_id=account_id,
            email=email,
            refresh_token=refresh_token,
            scopes=granted_scopes,
        )

        if not connected:
            return google_connection_redirect("connection_conflict")

    except (httpx.HTTPError, ValueError) as error:
        await db.rollback()

        logger.warning(
            "Google Calendar authorization failed: %s",
            type(error).__name__,
        )

        return google_connection_redirect("authorization_failed")

    except Exception:
        await db.rollback()

        logger.exception("Unable to complete Google Calendar connection")

        return google_connection_redirect("connection_failed")

    return google_connection_redirect("connected")


@router.get(
    "/status",
    response_model=CalendarIntegrationStatusResponse,
)
async def get_google_calendar_status(
    employee: Annotated[
        Employee,
        Depends(get_current_employee_read_only),
    ],
    db: Annotated[AsyncSession, Depends(get_db)],
    response: Response,
) -> CalendarIntegrationStatusResponse:
    response.headers["Cache-Control"] = "no-store"

    connection = await db.scalar(
        select(CalendarIntegration).where(
            CalendarIntegration.employee_id == employee.user_id,
            CalendarIntegration.provider == "google",
        )
    )

    if connection is None:
        return CalendarIntegrationStatusResponse(
            provider="google",
            connected=False,
        )

    result = await db.execute(
        select(
            func.max(CalendarSyncRecord.last_synced_at),
            func.count(CalendarSyncRecord.id).filter(
                CalendarSyncRecord.status == "pending",
            ),
            func.count(CalendarSyncRecord.id).filter(
                CalendarSyncRecord.status == "syncing",
            ),
            func.count(CalendarSyncRecord.id).filter(
                CalendarSyncRecord.status == "failed",
            ),
        ).where(
            CalendarSyncRecord.integration_id == connection.id,
        )
    )

    last_synced_at, pending_count, syncing_count, failed_count = result.one()

    return CalendarIntegrationStatusResponse(
        provider="google",
        connected=True,
        integration_id=connection.id,
        account_email=connection.account_email,
        connected_at=connection.connected_at,
        last_synced_at=last_synced_at,
        pending_count=pending_count,
        syncing_count=syncing_count,
        failed_count=failed_count,
    )


@router.delete(
    "",
    response_model=CalendarDisconnectResponse,
    dependencies=[Depends(validate_request_origin)],
)
async def disconnect_google_calendar(
    request: Request,
    employee: Annotated[Employee, Depends(get_current_employee)],
    db: Annotated[AsyncSession, Depends(get_db)],
    csrf_protect: Annotated[CsrfProtect, Depends()],
) -> CalendarDisconnectResponse:
    try:
        await csrf_protect.validate_csrf(request)
    except CsrfProtectError as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing CSRF token",
        ) from error

    connection = await db.scalar(
        select(CalendarIntegration)
        .where(
            CalendarIntegration.employee_id == employee.user_id,
            CalendarIntegration.provider == "google",
        )
        .with_for_update()
    )

    if connection is None:
        return CalendarDisconnectResponse(
            provider="google",
            disconnected=True,
        )

    try:
        encryption = CalendarTokenEncryption()

        refresh_token = encryption.decrypt(connection.encrypted_refresh_token)
    except CalendarTokenEncryptionError as error:
        await db.rollback()

        logger.error("Unable to decrypt Google Calendar credentials for disconnection")

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to access calendar connection credentials",
        ) from error

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                GOOGLE_REVOCATION_URL,
                data={
                    "token": refresh_token,
                },
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                },
            )

        if response.status_code not in (200, 400):
            response.raise_for_status()

    except httpx.HTTPError as error:
        await db.rollback()

        logger.warning(
            "Google Calendar token revocation failed: %s",
            type(error).__name__,
        )

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unable to disconnect Google Calendar. Please retry.",
        ) from error

    await db.delete(connection)
    await db.commit()

    return CalendarDisconnectResponse(
        provider="google",
        disconnected=True,
    )


@router.post(
    "/sync",
    response_model=CalendarSyncRequestResponse,
    dependencies=[Depends(validate_request_origin)],
)
async def sync_google_calendar(
    request: Request,
    employee: Annotated[Employee, Depends(get_current_employee)],
    db: Annotated[AsyncSession, Depends(get_db)],
    csrf_protect: Annotated[CsrfProtect, Depends()],
) -> CalendarSyncRequestResponse:
    try:
        await csrf_protect.validate_csrf(request)
    except CsrfProtectError as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing CSRF token",
        ) from error

    integration = await db.scalar(
        select(CalendarIntegration).where(
            CalendarIntegration.employee_id == employee.user_id,
            CalendarIntegration.provider == "google",
        )
    )

    if integration is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Connect Google Calendar before synchronizing",
        )

    try:
        task_ids = list(
            (
                await db.scalars(
                    select(Task.id).where(
                        Task.employee_id == employee.user_id,
                        Task.due_date.is_not(None),
                        Task.deleted_at.is_(None),
                        Task.archived_at.is_(None),
                    )
                )
            ).all()
        )

        event_ids = list(
            (
                await db.scalars(
                    select(CalendarEvent.id).where(
                        CalendarEvent.employee_id == employee.user_id,
                    )
                )
            ).all()
        )

        eligible_sources = {("task", task_id) for task_id in task_ids}

        eligible_sources.update(("calendar_event", event_id) for event_id in event_ids)

        existing_records = list(
            (
                await db.scalars(
                    select(CalendarSyncRecord).where(
                        CalendarSyncRecord.integration_id == integration.id,
                    )
                )
            ).all()
        )

        sync_service = CalendarSyncService(db)

        for task_id in task_ids:
            await sync_service.enqueue_upsert(
                employee_id=employee.user_id,
                source_type="task",
                source_id=task_id,
            )

        for event_id in event_ids:
            await sync_service.enqueue_upsert(
                employee_id=employee.user_id,
                source_type="calendar_event",
                source_id=event_id,
            )

        deletion_count = 0

        for record in existing_records:
            source = (
                record.source_type,
                record.source_id,
            )

            if source in eligible_sources:
                continue

            if (
                record.operation == "delete"
                and record.status == "synced"
                and record.external_event_id is None
            ):
                continue

            await sync_service.enqueue_delete(
                employee_id=employee.user_id,
                source_type=record.source_type,
                source_id=record.source_id,
            )

            deletion_count += 1

        await db.commit()

        return CalendarSyncRequestResponse(
            queued=True,
            task_count=len(task_ids),
            event_count=len(event_ids),
            deletion_count=deletion_count,
        )

    except Exception:
        await db.rollback()
        raise
