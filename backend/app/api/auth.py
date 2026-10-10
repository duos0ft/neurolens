from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.oauth import create_auth0_client
from app.core.settings import settings
from app.models.auth_flow import AuthFlow
from app.services.oauth import (
    generate_code_challenge,
    generate_token,
    hash_token,
)
from authlib.integrations.base_client.errors import OAuthError
from fastapi import Request
from sqlalchemy import select

from app.core.oauth import get_auth0_token_url
from app.models.employee import Employee
from app.services.auth0 import verify_id_token
from app.services.auth_flow import consume_auth_flow
from app.services.session import create_employee_session

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)

OAUTH_COOKIE_NAME = "neurolens_oauth"


@router.get("/login")
async def login(
    db: AsyncSession = Depends(get_db),
):
    state = generate_token()
    browser_nonce = generate_token()
    oidc_nonce = generate_token()
    code_verifier = generate_token()

    auth_flow = AuthFlow(
        state_hash=hash_token(state),
        browser_nonce_hash=hash_token(browser_nonce),
        oidc_nonce=oidc_nonce,
        code_verifier=code_verifier,
        expires_at=datetime.now(timezone.utc)
        + timedelta(seconds=settings.oauth_state_lifetime_seconds),
    )

    db.add(auth_flow)
    await db.commit()

    client = create_auth0_client()

    authorization_url, _ = client.create_authorization_url(
        url=f"https://{settings.auth0_domain}/authorize",
        state=state,
        nonce=oidc_nonce,
        code_challenge=generate_code_challenge(code_verifier),
        code_challenge_method="S256",
    )

    response = RedirectResponse(
        url=authorization_url,
        status_code=302,
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

    return response


@router.get("/callback")
async def callback(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    state = request.query_params.get("state")
    code = request.query_params.get("code")
    browser_nonce = request.cookies.get(OAUTH_COOKIE_NAME)

    def reject(reason: str) -> RedirectResponse:
        response = RedirectResponse(
            url=f"{settings.frontend_url}/login?error={reason}",
            status_code=303,
        )
        response.delete_cookie(
            key=OAUTH_COOKIE_NAME,
            path="/api/auth",
        )
        return response

    if not state or not browser_nonce:
        return reject("invalid_state")

    flow = await consume_auth_flow(
        db,
        state,
        browser_nonce,
    )

    if flow is None:
        return reject("invalid_state")

    if request.query_params.get("error"):
        return reject("authentication_failed")

    if not code:
        return reject("missing_code")

    try:
        async with create_auth0_client() as client:
            client.state = state

            token = await client.fetch_token(
                get_auth0_token_url(),
                code=code,
                state=state,
                code_verifier=flow.code_verifier,
            )

        id_token = token.get("id_token")

        if not id_token:
            return reject("invalid_token")

        claims = await verify_id_token(
            id_token,
            flow.oidc_nonce,
        )

    except (OAuthError, ValueError):
        return reject("authentication_failed")

    auth0_user_id = claims["sub"]

    employee = await db.scalar(
        select(Employee).where(
            Employee.auth0_user_id == auth0_user_id,
            Employee.status == "active",
        )
    )

    if employee is None:
        return reject("access_denied")

    session_token = await create_employee_session(
        db,
        employee.user_id,
    )

    response = RedirectResponse(
        url=f"{settings.frontend_url}{flow.return_path}",
        status_code=303,
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

    return response
