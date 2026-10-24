from collections.abc import AsyncIterator

import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.database import get_db
from app.core.settings import settings
from app.main import create_app
from app.models.application_settings import ApplicationSettings
from app.models.employee import Employee


@pytest.fixture
async def restore_application_settings(
    test_admin_session_factory: async_sessionmaker[AsyncSession],
) -> AsyncIterator[None]:
    async with test_admin_session_factory() as db:
        application_settings = await db.get(ApplicationSettings, 1)

        assert application_settings is not None

        original_values = {
            "organization_name": application_settings.organization_name,
            "enable_task_assistance": application_settings.enable_task_assistance,
            "enable_policy_assistance": application_settings.enable_policy_assistance,
            "enable_sentiment_analysis": application_settings.enable_sentiment_analysis,
        }

    try:
        yield

    finally:
        async with test_admin_session_factory() as db:
            application_settings = await db.get(ApplicationSettings, 1)

            assert application_settings is not None

            for field, value in original_values.items():
                setattr(application_settings, field, value)

            await db.commit()


@pytest.mark.asyncio
async def test_admin_can_get_application_settings(
    admin_client: httpx.AsyncClient,
) -> None:
    response = await admin_client.get("/api/admin/settings")

    assert response.status_code == 200

    data = response.json()

    assert data["organization_name"]
    assert isinstance(data["enable_task_assistance"], bool)
    assert isinstance(data["enable_policy_assistance"], bool)
    assert isinstance(data["enable_sentiment_analysis"], bool)
    assert "created_at" in data
    assert "updated_at" in data


@pytest.mark.asyncio
async def test_admin_can_update_application_settings(
    admin_client: httpx.AsyncClient,
    restore_application_settings,
    test_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    response = await admin_client.patch(
        "/api/admin/settings",
        json={
            "organization_name": "  NeuroLens Research  ",
            "enable_sentiment_analysis": True,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["organization_name"] == "NeuroLens Research"
    assert data["enable_sentiment_analysis"] is True

    async with test_session_factory() as db:
        application_settings = await db.get(ApplicationSettings, 1)

        assert application_settings is not None
        assert application_settings.organization_name == "NeuroLens Research"
        assert application_settings.enable_sentiment_analysis is True


@pytest.mark.asyncio
async def test_partial_update_preserves_other_settings(
    admin_client: httpx.AsyncClient,
    restore_application_settings,
) -> None:
    original = await admin_client.get("/api/admin/settings")

    assert original.status_code == 200

    before = original.json()

    response = await admin_client.patch(
        "/api/admin/settings",
        json={
            "enable_task_assistance": not before["enable_task_assistance"],
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["enable_task_assistance"] != before["enable_task_assistance"]
    assert data["organization_name"] == before["organization_name"]
    assert data["enable_policy_assistance"] == before["enable_policy_assistance"]
    assert data["enable_sentiment_analysis"] == before["enable_sentiment_analysis"]


@pytest.mark.asyncio
async def test_admin_settings_rejects_empty_name(
    admin_client: httpx.AsyncClient,
) -> None:
    response = await admin_client.patch(
        "/api/admin/settings",
        json={
            "organization_name": "   ",
        },
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_admin_settings_rejects_null_values(
    admin_client: httpx.AsyncClient,
) -> None:
    response = await admin_client.patch(
        "/api/admin/settings",
        json={
            "enable_task_assistance": None,
        },
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_admin_settings_requires_csrf(
    admin_client: httpx.AsyncClient,
) -> None:
    response = await admin_client.patch(
        "/api/admin/settings",
        json={
            "organization_name": "Unauthorized change",
        },
        headers={
            "X-CSRF-Token": "",
        },
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_regular_employee_cannot_access_admin_settings(
    admin_client: httpx.AsyncClient,
    test_admin_session_factory: async_sessionmaker[AsyncSession],
    test_invitation,
) -> None:
    async with test_admin_session_factory() as db:
        employee = await db.get(Employee, test_invitation.employee_id)

        assert employee is not None

        employee.role = "employee"

        await db.commit()

    get_response = await admin_client.get("/api/admin/settings")

    patch_response = await admin_client.patch(
        "/api/admin/settings",
        json={
            "organization_name": "Unauthorized change",
        },
    )

    assert get_response.status_code == 403
    assert patch_response.status_code == 403


@pytest.mark.asyncio
async def test_unauthenticated_user_cannot_access_admin_settings(
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
            response = await client.get("/api/admin/settings")

        assert response.status_code == 401

    finally:
        app.dependency_overrides.clear()