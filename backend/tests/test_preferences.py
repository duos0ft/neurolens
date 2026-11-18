from datetime import datetime, timedelta, timezone

import httpx
import pytest
from fastapi_csrf_protect import CsrfProtect
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.database import get_db
from app.core.settings import settings
from app.main import create_app
from app.models.employee import Employee
from app.models.employee_profile import EmployeeProfile
from app.models.employee_session import EmployeeSession
from app.services.authentication.oauth import generate_token, hash_token


@pytest.fixture
async def authenticated_client(
    test_session_factory: async_sessionmaker[AsyncSession],
    test_invitation,
):
    employee_id = test_invitation.employee_id
    session_token = generate_token()
    now = datetime.now(timezone.utc)

    async with test_session_factory() as db:
        employee = await db.get(Employee, employee_id)

        assert employee is not None

        employee.status = "active"

        db.add(
            EmployeeSession(
                employee_id=employee_id,
                session_hash=hash_token(session_token),
                last_active_at=now,
                expires_at=now + timedelta(days=7),
            )
        )

        await db.commit()

    app = create_app()

    async def override_get_db():
        async with test_session_factory() as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db

    try:
        transport = httpx.ASGITransport(app=app)

        async with httpx.AsyncClient(
            transport=transport,
            base_url=settings.frontend_url,
            headers={
                "Origin": settings.frontend_url,
            },
        ) as client:
            client.cookies.set(
                settings.session_cookie_name,
                session_token,
                path="/",
            )

            csrf_protect = CsrfProtect()
            csrf_token, signed_token = csrf_protect.generate_csrf_tokens()

            client.cookies.set(
                csrf_protect._cookie_key,
                signed_token,
                path="/",
            )

            client.headers["X-CSRF-Token"] = csrf_token

            yield client, employee_id

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_preferences_returns_defaults(
    authenticated_client,
) -> None:
    client, _ = authenticated_client

    response = await client.get("/api/preferences")

    assert response.status_code == 200
    assert response.json() == {
        "directness": "balanced",
        "response_length": "medium",
        "highlight_ambiguity": True,
        "step_by_step_guidance": True,
        "always_show_next_step": True,
    }


@pytest.mark.asyncio
async def test_get_preferences_returns_saved_values(
    authenticated_client,
    test_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    client, employee_id = authenticated_client

    async with test_session_factory() as db:
        profile = await db.get(EmployeeProfile, employee_id)

        if profile is None:
            profile = EmployeeProfile(user_id=employee_id)
            db.add(profile)

        profile.directness = "high"
        profile.response_length = "detailed"
        profile.highlight_ambiguity = False

        await db.commit()

    response = await client.get("/api/preferences")

    assert response.status_code == 200
    assert response.json() == {
        "directness": "high",
        "response_length": "detailed",
        "highlight_ambiguity": False,
        "step_by_step_guidance": True,
        "always_show_next_step": True,
    }


@pytest.mark.asyncio
async def test_unauthenticated_employee_cannot_read_preferences(
    test_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    app = create_app()

    async def override_get_db():
        async with test_session_factory() as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db

    try:
        transport = httpx.ASGITransport(app=app)

        async with httpx.AsyncClient(
            transport=transport,
            base_url=settings.frontend_url,
            headers={
                "Origin": settings.frontend_url,
            },
        ) as client:
            response = await client.get("/api/preferences")

        assert response.status_code == 401

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_update_preferences_preserves_other_values(
    authenticated_client,
    test_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    client, employee_id = authenticated_client

    async with test_session_factory() as db:
        profile = await db.get(EmployeeProfile, employee_id)

        if profile is None:
            profile = EmployeeProfile(user_id=employee_id)
            db.add(profile)

        profile.response_length = "detailed"
        profile.highlight_ambiguity = False

        await db.commit()

    response = await client.patch(
        "/api/preferences",
        json={
            "directness": "high",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "directness": "high",
        "response_length": "detailed",
        "highlight_ambiguity": False,
        "step_by_step_guidance": True,
        "always_show_next_step": True,
    }

    async with test_session_factory() as db:
        profile = await db.get(EmployeeProfile, employee_id)

        assert profile is not None
        assert profile.directness == "high"
        assert profile.response_length == "detailed"
        assert profile.highlight_ambiguity is False


@pytest.mark.asyncio
async def test_update_preferences_rejects_invalid_values(
    authenticated_client,
) -> None:
    client, _ = authenticated_client

    response = await client.patch(
        "/api/preferences",
        json={
            "directness": "extreme",
        },
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_update_preferences_rejects_null_values(
    authenticated_client,
) -> None:
    client, _ = authenticated_client

    response = await client.patch(
        "/api/preferences",
        json={
            "response_length": None,
        },
    )

    assert response.status_code == 422
