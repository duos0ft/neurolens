import logging
from datetime import datetime, timedelta, timezone
from typing import Annotated
from urllib.parse import urlencode

import httpx
from authlib.integrations.httpx_client import OAuthError
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    Response,
    status,
)
from fastapi.responses import RedirectResponse
from fastapi_csrf_protect import CsrfProtect
from fastapi_csrf_protect.exceptions import CsrfProtectError
from joserfc.errors import JoseError
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import csrf_config  # Register CSRF configuration
from app.core.auth import get_current_employee
from app.core.csrf import validate_request_origin
from app.core.database import get_db
from app.core.oauth import create_auth0_client, get_auth0_token_url
from app.core.settings import settings
from app.models.auth_flow import AuthFlow
from app.models.employee import Employee
from app.models.employee_session import EmployeeSession
from app.services.auth0 import verify_id_token
from app.services.auth_flow import consume_auth_flow
from app.services.oauth import (
    generate_code_challenge,
    generate_token,
    hash_token,
)
from app.services.session import create_employee_session


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)

OAUTH_COOKIE_NAME = "neurolens_oauth"


def reject_authentication(reason: str) -> RedirectResponse:
    response = RedirectResponse(
        url=f"{settings.frontend_url}/auth/error?reason={reason}",
        status_code=status.HTTP_303_SEE_OTHER,
    )

    response.delete_cookie(
        key=OAUTH_COOKIE_NAME,
        path="/api/auth",
    )

    response.headers["Cache-Control"] = "no-store"

    return response


def get_auth0_logout_url() -> str:
    parameters = urlencode(
        {
            "client_id": settings.auth0_client_id,
            "post_logout_redirect_uri": (f"{settings.frontend_url}/auth/logged-out"),
        }
    )

    return f"https://{settings.auth0_domain}/oidc/logout?{parameters}"


@router.get("/login")
async def login(
    db: Annotated[AsyncSession, Depends(get_db)],
):
    state = generate_token()
    browser_nonce = generate_token()
    oidc_nonce = generate_token()
    code_verifier = generate_token()

    async with create_auth0_client() as client:
        authorization_url, _ = client.create_authorization_url(
            f"https://{settings.auth0_domain}/authorize",
            state=state,
            nonce=oidc_nonce,
            code_challenge=generate_code_challenge(code_verifier),
            code_challenge_method="S256",
        )

    auth_flow = AuthFlow(
        state_hash=hash_token(state),
        browser_nonce_hash=hash_token(browser_nonce),
        oidc_nonce=oidc_nonce,
        code_verifier=code_verifier,
        expires_at=(
            datetime.now(timezone.utc)
            + timedelta(
                seconds=settings.oauth_state_lifetime_seconds,
            )
        ),
    )

    db.add(auth_flow)
    await db.commit()

    response = RedirectResponse(
        url=authorization_url,
        status_code=status.HTTP_302_FOUND,
    )

    response.set_cookie(
        key=OAUTH_COOKIE_NAME,
        value=browser_nonce,
        max_age=settings.oauth_state_lifetime_seconds,
        httponly=True,
        secure=settings.session_cookie_secure,
        samesite="lax",
        path="/api/auth",
    )

    response.headers["Cache-Control"] = "no-store"

    return response


@router.get("/callback")
async def callback(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    state = request.query_params.get("state")
    code = request.query_params.get("code")
    browser_nonce = request.cookies.get(OAUTH_COOKIE_NAME)

    if not state or not browser_nonce:
        return reject_authentication("invalid_state")

    flow = await consume_auth_flow(
        db,
        state,
        browser_nonce,
    )

    if flow is None:
        return reject_authentication("invalid_state")

    if request.query_params.get("error"):
        return reject_authentication("authentication_failed")

    if not code:
        return reject_authentication("missing_code")

    try:
        async with create_auth0_client() as client:
            token = await client.fetch_token(
                get_auth0_token_url(),
                grant_type="authorization_code",
                code=code,
                redirect_uri=settings.auth0_redirect_uri,
                code_verifier=flow.code_verifier,
            )

        id_token = token.get("id_token")

        if not id_token:
            return reject_authentication("invalid_token")

        claims = await verify_id_token(
            id_token,
            flow.oidc_nonce,
        )

    except (
        OAuthError,
        httpx.HTTPError,
        JoseError,
        ValueError,
    ) as exc:
        logger.warning(
            "Auth0 authentication failed: %s",
            type(exc).__name__,
        )

        return reject_authentication("authentication_failed")

    employee = await db.scalar(
        select(Employee).where(
            Employee.auth0_user_id == claims["sub"],
            Employee.status == "active",
        )
    )

    if employee is None:
        return reject_authentication("access_denied")

    session_token = await create_employee_session(
        db,
        employee.user_id,
    )

    response = RedirectResponse(
        url=f"{settings.frontend_url}{flow.return_path}",
        status_code=status.HTTP_303_SEE_OTHER,
    )

    response.delete_cookie(
        key=OAUTH_COOKIE_NAME,
        path="/api/auth",
    )

    response.set_cookie(
        key=settings.session_cookie_name,
        value=session_token,
        max_age=settings.session_lifetime_seconds,
        httponly=True,
        secure=settings.session_cookie_secure,
        samesite="lax",
        path="/",
    )

    response.headers["Cache-Control"] = "no-store"

    return response


@router.get("/me")
async def get_me(
    employee: Annotated[Employee, Depends(get_current_employee)],
    response: Response,
):
    response.headers["Cache-Control"] = "no-store"

    return {
        "id": employee.user_id,
        "role": employee.role,
        "status": employee.status,
    }


@router.get("/csrf")
async def get_csrf_token(
    response: Response,
    employee: Annotated[Employee, Depends(get_current_employee)],
    csrf_protect: Annotated[CsrfProtect, Depends()],
):
    csrf_token, signed_token = csrf_protect.generate_csrf_tokens()

    csrf_protect.set_csrf_cookie(
        signed_token,
        response,
    )

    response.headers["Cache-Control"] = "no-store"

    return {
        "csrf_token": csrf_token,
    }


@router.post(
    "/logout",
    dependencies=[Depends(validate_request_origin)],
)
async def logout(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    csrf_protect: Annotated[CsrfProtect, Depends()],
):
    try:
        await csrf_protect.validate_csrf(request)

    except CsrfProtectError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing CSRF token",
        ) from exc

    session_token = request.cookies.get(
        settings.session_cookie_name,
    )

    if session_token:
        await db.execute(
            update(EmployeeSession)
            .where(
                EmployeeSession.session_hash == hash_token(session_token),
                EmployeeSession.revoked_at.is_(None),
            )
            .values(
                revoked_at=datetime.now(timezone.utc),
            )
        )

        await db.commit()

    response = RedirectResponse(
        url=get_auth0_logout_url(),
        status_code=status.HTTP_303_SEE_OTHER,
    )

    response.delete_cookie(
        key=settings.session_cookie_name,
        path="/",
    )

    response.delete_cookie(
        key=OAUTH_COOKIE_NAME,
        path="/api/auth",
    )

    csrf_protect.unset_csrf_cookie(response)

    response.headers["Cache-Control"] = "no-store"

    return response
