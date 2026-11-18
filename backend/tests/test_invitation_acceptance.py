from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import httpx
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.database import get_db
from app.main import create_app
from app.models.auth_flow import AuthFlow
from app.models.employee import Employee
from app.models.employee_invitation import EmployeeInvitation
from app.models.employee_session import EmployeeSession
from app.services.authentication.oauth import generate_token, hash_token


@pytest.mark.asyncio
async def test_employee_accepts_invitation(
    test_session_factory: async_sessionmaker[AsyncSession],
    test_invitation: EmployeeInvitation,
) -> None:
    employee_id = test_invitation.employee_id
    invitation_id = test_invitation.id

    auth0_user_id = f"email|{employee_id.hex}"
    state = generate_token()
    browser_nonce = generate_token()
    oidc_nonce = generate_token()

    async with test_session_factory() as db:
        employee = await db.get(Employee, employee_id)
        invitation = await db.get(EmployeeInvitation, invitation_id)

        assert employee is not None
        assert invitation is not None

        employee.auth0_user_id = auth0_user_id
        employee.provisioning_status = "completed"

        invitation.status = "ready"

        flow = AuthFlow(
            state_hash=hash_token(state),
            browser_nonce_hash=hash_token(browser_nonce),
            oidc_nonce=oidc_nonce,
            code_verifier=generate_token(),
            invitation_id=invitation_id,
            expires_at=(datetime.now(timezone.utc) + timedelta(minutes=10)),
        )

        db.add(flow)
        await db.commit()

        email = employee.email
        flow_id = flow.id

    app = create_app()

    async def override_get_db():
        async with test_session_factory() as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db

    mock_oauth_client = AsyncMock()
    mock_oauth_client.fetch_token.return_value = {
        "id_token": "mock-valid-id-token",
    }

    mock_context_manager = AsyncMock()
    mock_context_manager.__aenter__.return_value = mock_oauth_client

    try:
        with (
            patch(
                "app.api.auth.create_auth0_client",
                return_value=mock_context_manager,
            ),
            patch(
                "app.api.auth.verify_id_token",
                new_callable=AsyncMock,
                return_value={
                    "sub": auth0_user_id,
                    "email": email,
                    "email_verified": True,
                },
            ),
        ):
            transport = httpx.ASGITransport(app=app)

            async with httpx.AsyncClient(
                transport=transport,
                base_url="http://testserver",
                follow_redirects=False,
            ) as client:
                client.cookies.set(
                    "neurolens_oauth",
                    browser_nonce,
                    path="/api/auth",
                )

                response = await client.get(
                    "/api/auth/callback",
                    params={
                        "state": state,
                        "code": "mock-authorization-code",
                    },
                )

        assert response.status_code == 303
        assert response.headers["location"].endswith("/app")

        async with test_session_factory() as db:
            employee = await db.get(Employee, employee_id)
            invitation = await db.get(EmployeeInvitation, invitation_id)
            flow = await db.get(AuthFlow, flow_id)

            sessions = (
                await db.scalars(
                    select(EmployeeSession).where(
                        EmployeeSession.employee_id == employee_id,
                    )
                )
            ).all()

            assert employee is not None
            assert employee.status == "active"

            assert invitation is not None
            assert invitation.status == "accepted"
            assert invitation.accepted_at is not None

            assert flow is not None
            assert flow.consumed_at is not None

            assert len(sessions) == 1
            assert sessions[0].revoked_at is None

    finally:
        app.dependency_overrides.clear()

        async with test_session_factory() as db:
            flow = await db.get(AuthFlow, flow_id)

            if flow is not None:
                await db.delete(flow)
                await db.commit()


@pytest.mark.asyncio
async def test_invitation_rejects_wrong_auth0_identity(
    test_session_factory: async_sessionmaker[AsyncSession],
    test_invitation: EmployeeInvitation,
) -> None:
    employee_id = test_invitation.employee_id
    invitation_id = test_invitation.id

    state = generate_token()
    browser_nonce = generate_token()

    async with test_session_factory() as db:
        employee = await db.get(Employee, employee_id)
        invitation = await db.get(EmployeeInvitation, invitation_id)

        assert employee is not None
        assert invitation is not None

        employee.auth0_user_id = f"email|{employee_id.hex}"
        employee.provisioning_status = "completed"
        invitation.status = "ready"

        flow = AuthFlow(
            state_hash=hash_token(state),
            browser_nonce_hash=hash_token(browser_nonce),
            oidc_nonce=generate_token(),
            code_verifier=generate_token(),
            invitation_id=invitation_id,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=10),
        )

        db.add(flow)
        await db.commit()

        invited_email = employee.email
        flow_id = flow.id

    app = create_app()

    async def override_get_db():
        async with test_session_factory() as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db

    mock_oauth_client = AsyncMock()
    mock_oauth_client.fetch_token.return_value = {
        "id_token": "mock-valid-id-token",
    }

    mock_context_manager = AsyncMock()
    mock_context_manager.__aenter__.return_value = mock_oauth_client

    try:
        with (
            patch(
                "app.api.auth.create_auth0_client",
                return_value=mock_context_manager,
            ),
            patch(
                "app.api.auth.verify_id_token",
                new_callable=AsyncMock,
                return_value={
                    "sub": "email|different-user",
                    "email": invited_email,
                    "email_verified": True,
                },
            ),
        ):
            transport = httpx.ASGITransport(app=app)

            async with httpx.AsyncClient(
                transport=transport,
                base_url="http://testserver",
                follow_redirects=False,
            ) as client:
                client.cookies.set(
                    "neurolens_oauth",
                    browser_nonce,
                    path="/api/auth",
                )

                response = await client.get(
                    "/api/auth/callback",
                    params={
                        "state": state,
                        "code": "mock-authorization-code",
                    },
                )

        assert response.status_code == 303
        assert "reason=access_denied" in response.headers["location"]

        async with test_session_factory() as db:
            employee = await db.get(Employee, employee_id)
            invitation = await db.get(EmployeeInvitation, invitation_id)
            flow = await db.get(AuthFlow, flow_id)

            sessions = (
                await db.scalars(
                    select(EmployeeSession).where(
                        EmployeeSession.employee_id == employee_id,
                    )
                )
            ).all()

            assert employee.status == "invited"
            assert invitation.status == "ready"
            assert invitation.accepted_at is None
            assert flow.consumed_at is not None
            assert len(sessions) == 0

    finally:
        app.dependency_overrides.clear()

        async with test_session_factory() as db:
            flow = await db.get(AuthFlow, flow_id)

            if flow is not None:
                await db.delete(flow)
                await db.commit()


@pytest.mark.asyncio
async def test_expired_invitation_cannot_be_accepted(
    test_session_factory: async_sessionmaker[AsyncSession],
    test_invitation: EmployeeInvitation,
) -> None:
    employee_id = test_invitation.employee_id
    invitation_id = test_invitation.id

    auth0_user_id = f"email|{employee_id.hex}"
    state = generate_token()
    browser_nonce = generate_token()

    async with test_session_factory() as db:
        employee = await db.get(Employee, employee_id)
        invitation = await db.get(EmployeeInvitation, invitation_id)

        assert employee is not None
        assert invitation is not None

        employee.auth0_user_id = auth0_user_id
        employee.provisioning_status = "completed"

        invitation.status = "ready"
        invitation.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)

        flow = AuthFlow(
            state_hash=hash_token(state),
            browser_nonce_hash=hash_token(browser_nonce),
            oidc_nonce=generate_token(),
            code_verifier=generate_token(),
            invitation_id=invitation_id,
            expires_at=(datetime.now(timezone.utc) + timedelta(minutes=10)),
        )

        db.add(flow)
        await db.commit()

        email = employee.email
        flow_id = flow.id

    app = create_app()

    async def override_get_db():
        async with test_session_factory() as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db

    mock_oauth_client = AsyncMock()
    mock_oauth_client.fetch_token.return_value = {
        "id_token": "mock-valid-id-token",
    }

    mock_context_manager = AsyncMock()
    mock_context_manager.__aenter__.return_value = mock_oauth_client

    try:
        with (
            patch(
                "app.api.auth.create_auth0_client",
                return_value=mock_context_manager,
            ),
            patch(
                "app.api.auth.verify_id_token",
                new_callable=AsyncMock,
                return_value={
                    "sub": auth0_user_id,
                    "email": email,
                    "email_verified": True,
                },
            ),
        ):
            transport = httpx.ASGITransport(app=app)

            async with httpx.AsyncClient(
                transport=transport,
                base_url="http://testserver",
                follow_redirects=False,
            ) as client:
                client.cookies.set(
                    "neurolens_oauth",
                    browser_nonce,
                    path="/api/auth",
                )

                response = await client.get(
                    "/api/auth/callback",
                    params={
                        "state": state,
                        "code": "mock-authorization-code",
                    },
                )

        assert response.status_code == 303
        assert "reason=access_denied" in response.headers["location"]

        async with test_session_factory() as db:
            employee = await db.get(Employee, employee_id)
            invitation = await db.get(EmployeeInvitation, invitation_id)
            flow = await db.get(AuthFlow, flow_id)

            sessions = (
                await db.scalars(
                    select(EmployeeSession).where(
                        EmployeeSession.employee_id == employee_id,
                    )
                )
            ).all()

            assert employee.status == "invited"
            assert invitation.status == "ready"
            assert invitation.accepted_at is None
            assert flow.consumed_at is not None
            assert len(sessions) == 0

    finally:
        app.dependency_overrides.clear()

        async with test_session_factory() as db:
            flow = await db.get(AuthFlow, flow_id)

            if flow is not None:
                await db.delete(flow)
                await db.commit()


@pytest.mark.asyncio
async def test_invitation_oauth_callback_cannot_be_replayed(
    test_session_factory: async_sessionmaker[AsyncSession],
    test_invitation: EmployeeInvitation,
) -> None:
    employee_id = test_invitation.employee_id
    invitation_id = test_invitation.id

    auth0_user_id = f"email|{employee_id.hex}"
    state = generate_token()
    browser_nonce = generate_token()

    async with test_session_factory() as db:
        employee = await db.get(Employee, employee_id)
        invitation = await db.get(EmployeeInvitation, invitation_id)

        assert employee is not None
        assert invitation is not None

        employee.auth0_user_id = auth0_user_id
        employee.provisioning_status = "completed"
        invitation.status = "ready"

        flow = AuthFlow(
            state_hash=hash_token(state),
            browser_nonce_hash=hash_token(browser_nonce),
            oidc_nonce=generate_token(),
            code_verifier=generate_token(),
            invitation_id=invitation_id,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=10),
        )

        db.add(flow)
        await db.commit()

        email = employee.email
        flow_id = flow.id

    app = create_app()

    async def override_get_db():
        async with test_session_factory() as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db

    mock_oauth_client = AsyncMock()
    mock_oauth_client.fetch_token.return_value = {
        "id_token": "mock-valid-id-token",
    }

    mock_context_manager = AsyncMock()
    mock_context_manager.__aenter__.return_value = mock_oauth_client

    try:
        with (
            patch(
                "app.api.auth.create_auth0_client",
                return_value=mock_context_manager,
            ),
            patch(
                "app.api.auth.verify_id_token",
                new_callable=AsyncMock,
                return_value={
                    "sub": auth0_user_id,
                    "email": email,
                    "email_verified": True,
                },
            ),
        ):
            transport = httpx.ASGITransport(app=app)

            async with httpx.AsyncClient(
                transport=transport,
                base_url="http://testserver",
                follow_redirects=False,
            ) as client:
                client.cookies.set(
                    "neurolens_oauth",
                    browser_nonce,
                    path="/api/auth",
                )

                first_response = await client.get(
                    "/api/auth/callback",
                    params={
                        "state": state,
                        "code": "mock-authorization-code",
                    },
                )

                # Restore the original OAuth cookie to simulate
                # a replay of the exact same callback.
                client.cookies.set(
                    "neurolens_oauth",
                    browser_nonce,
                    path="/api/auth",
                )

                second_response = await client.get(
                    "/api/auth/callback",
                    params={
                        "state": state,
                        "code": "mock-authorization-code",
                    },
                )

        assert first_response.status_code == 303
        assert first_response.headers["location"].endswith("/app")

        assert second_response.status_code == 303
        assert "reason=invalid_state" in second_response.headers["location"]

        assert mock_oauth_client.fetch_token.await_count == 1

        async with test_session_factory() as db:
            employee = await db.get(Employee, employee_id)
            invitation = await db.get(EmployeeInvitation, invitation_id)
            flow = await db.get(AuthFlow, flow_id)

            sessions = (
                await db.scalars(
                    select(EmployeeSession).where(
                        EmployeeSession.employee_id == employee_id,
                    )
                )
            ).all()

            assert employee.status == "active"
            assert invitation.status == "accepted"
            assert invitation.accepted_at is not None
            assert flow.consumed_at is not None

            # Replaying the callback must not create another session.
            assert len(sessions) == 1

    finally:
        app.dependency_overrides.clear()

        async with test_session_factory() as db:
            flow = await db.get(AuthFlow, flow_id)

            if flow is not None:
                await db.delete(flow)
                await db.commit()


@pytest.mark.asyncio
async def test_invitation_acceptance_rolls_back_when_session_creation_fails(
    test_session_factory: async_sessionmaker[AsyncSession],
    test_invitation: EmployeeInvitation,
) -> None:
    employee_id = test_invitation.employee_id
    invitation_id = test_invitation.id

    auth0_user_id = f"email|{employee_id.hex}"
    state = generate_token()
    browser_nonce = generate_token()

    async with test_session_factory() as db:
        employee = await db.get(Employee, employee_id)
        invitation = await db.get(EmployeeInvitation, invitation_id)

        assert employee is not None
        assert invitation is not None

        employee.auth0_user_id = auth0_user_id
        employee.provisioning_status = "completed"
        invitation.status = "ready"

        flow = AuthFlow(
            state_hash=hash_token(state),
            browser_nonce_hash=hash_token(browser_nonce),
            oidc_nonce=generate_token(),
            code_verifier=generate_token(),
            invitation_id=invitation_id,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=10),
        )

        db.add(flow)
        await db.commit()

        email = employee.email
        flow_id = flow.id

    app = create_app()

    async def override_get_db():
        async with test_session_factory() as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db

    mock_oauth_client = AsyncMock()
    mock_oauth_client.fetch_token.return_value = {
        "id_token": "mock-valid-id-token",
    }

    mock_context_manager = AsyncMock()
    mock_context_manager.__aenter__.return_value = mock_oauth_client

    async def fail_session_creation(*args, **kwargs):
        raise RuntimeError("Simulated session creation failure")

    try:
        with (
            patch(
                "app.api.auth.create_auth0_client",
                return_value=mock_context_manager,
            ),
            patch(
                "app.api.auth.verify_id_token",
                new_callable=AsyncMock,
                return_value={
                    "sub": auth0_user_id,
                    "email": email,
                    "email_verified": True,
                },
            ),
            patch(
                "app.api.auth.create_employee_session",
                side_effect=fail_session_creation,
            ),
        ):
            transport = httpx.ASGITransport(app=app)

            async with httpx.AsyncClient(
                transport=transport,
                base_url="http://testserver",
            ) as client:
                client.cookies.set(
                    "neurolens_oauth",
                    browser_nonce,
                    path="/api/auth",
                )

                with pytest.raises(
                    RuntimeError,
                    match="Simulated session creation failure",
                ):
                    await client.get(
                        "/api/auth/callback",
                        params={
                            "state": state,
                            "code": "mock-authorization-code",
                        },
                    )

        async with test_session_factory() as db:
            employee = await db.get(Employee, employee_id)
            invitation = await db.get(EmployeeInvitation, invitation_id)
            flow = await db.get(AuthFlow, flow_id)

            sessions = (
                await db.scalars(
                    select(EmployeeSession).where(
                        EmployeeSession.employee_id == employee_id,
                    )
                )
            ).all()

            assert employee is not None
            assert employee.status == "invited"

            assert invitation is not None
            assert invitation.status == "ready"
            assert invitation.accepted_at is None

            assert len(sessions) == 0

            # OAuth state stays consumed to prevent replay.
            assert flow is not None
            assert flow.consumed_at is not None

    finally:
        app.dependency_overrides.clear()

        async with test_session_factory() as db:
            flow = await db.get(AuthFlow, flow_id)

            if flow is not None:
                await db.delete(flow)
                await db.commit()
