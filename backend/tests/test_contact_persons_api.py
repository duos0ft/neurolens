import uuid
from collections.abc import AsyncIterator

import httpx
import pytest
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.database import get_db
from app.core.settings import settings
from app.main import create_app
from app.models.contact_person import ContactPerson
from app.models.employee import Employee


@pytest.fixture
async def contact_cleanup(
    test_admin_session_factory: async_sessionmaker[AsyncSession],
) -> AsyncIterator[list[uuid.UUID]]:
    contact_ids: list[uuid.UUID] = []

    try:
        yield contact_ids

    finally:
        if contact_ids:
            async with test_admin_session_factory() as db:
                await db.execute(
                    delete(ContactPerson).where(
                        ContactPerson.id.in_(contact_ids),
                    )
                )

                await db.commit()


def contact_payload(
    email: str | None = None,
    responsibility: str = "General HR",
    is_primary: bool = False,
) -> dict:
    return {
        "name": "Sarah Williams",
        "email": email or f"contact-{uuid.uuid4().hex}@example.com",
        "job_title": "HR Manager",
        "department": "Human Resources",
        "responsibility": responsibility,
        "is_primary": is_primary,
    }


@pytest.mark.asyncio
async def test_admin_can_create_contact_person(
    admin_client: httpx.AsyncClient,
    contact_cleanup: list[uuid.UUID],
) -> None:
    payload = contact_payload()

    response = await admin_client.post(
        "/api/admin/contact-persons",
        json=payload,
    )

    assert response.status_code == 201

    data = response.json()
    contact_cleanup.append(uuid.UUID(data["id"]))

    assert data["name"] == payload["name"]
    assert data["email"] == payload["email"]
    assert data["responsibility"] == payload["responsibility"]
    assert data["job_title"] == payload["job_title"]
    assert data["department"] == payload["department"]
    assert data["is_active"] is True
    assert data["is_primary"] is False
    assert "created_at" in data
    assert "updated_at" in data


@pytest.mark.asyncio
async def test_admin_can_list_contact_persons(
    admin_client: httpx.AsyncClient,
    contact_cleanup: list[uuid.UUID],
) -> None:
    created = await admin_client.post(
        "/api/admin/contact-persons",
        json=contact_payload(),
    )

    assert created.status_code == 201

    contact_id = created.json()["id"]
    contact_cleanup.append(uuid.UUID(contact_id))

    response = await admin_client.get("/api/admin/contact-persons")

    assert response.status_code == 200

    data = response.json()

    assert "items" in data
    assert "page" in data
    assert "page_size" in data
    assert "total_items" in data
    assert "total_pages" in data

    assert data["page"] == 1
    assert data["page_size"] == 20
    assert data["total_items"] >= 1

    assert any(contact["id"] == contact_id for contact in data["items"])


@pytest.mark.asyncio
async def test_admin_can_update_contact_person(
    admin_client: httpx.AsyncClient,
    contact_cleanup: list[uuid.UUID],
) -> None:
    created = await admin_client.post(
        "/api/admin/contact-persons",
        json=contact_payload(),
    )

    assert created.status_code == 201

    contact_id = created.json()["id"]
    contact_cleanup.append(uuid.UUID(contact_id))

    payload = {
        **contact_payload(
            email=created.json()["email"],
            responsibility="Payroll",
        ),
        "name": "Sarah Johnson",
        "job_title": "Payroll Manager",
        "department": "Finance",
        "is_active": True,
    }

    response = await admin_client.patch(
        f"/api/admin/contact-persons/{contact_id}",
        json=payload,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == contact_id
    assert data["name"] == "Sarah Johnson"
    assert data["responsibility"] == "Payroll"
    assert data["job_title"] == "Payroll Manager"
    assert data["department"] == "Finance"


@pytest.mark.asyncio
async def test_admin_can_deactivate_contact_person(
    admin_client: httpx.AsyncClient,
    contact_cleanup: list[uuid.UUID],
) -> None:
    created = await admin_client.post(
        "/api/admin/contact-persons",
        json=contact_payload(
            responsibility=f"HR-{uuid.uuid4().hex}",
            is_primary=True,
        ),
    )

    assert created.status_code == 201

    contact_id = created.json()["id"]
    contact_cleanup.append(uuid.UUID(contact_id))

    response = await admin_client.post(f"/api/admin/contact-persons/{contact_id}/deactivate")

    assert response.status_code == 200
    assert response.json()["is_active"] is False
    assert response.json()["is_primary"] is False

    active_contacts = await admin_client.get("/api/admin/contact-persons")

    assert active_contacts.status_code == 200

    assert all(contact["id"] != contact_id for contact in active_contacts.json()["items"])

    all_contacts = await admin_client.get(
        "/api/admin/contact-persons",
        params={
            "include_inactive": "true",
        },
    )

    assert all_contacts.status_code == 200

    assert any(contact["id"] == contact_id for contact in all_contacts.json()["items"])


@pytest.mark.asyncio
async def test_duplicate_contact_email_returns_conflict(
    admin_client: httpx.AsyncClient,
    contact_cleanup: list[uuid.UUID],
) -> None:
    payload = contact_payload()

    created = await admin_client.post(
        "/api/admin/contact-persons",
        json=payload,
    )

    assert created.status_code == 201

    contact_cleanup.append(uuid.UUID(created.json()["id"]))

    duplicate = await admin_client.post(
        "/api/admin/contact-persons",
        json={
            **payload,
            "name": "Another HR Contact",
        },
    )

    assert duplicate.status_code == 409


@pytest.mark.asyncio
async def test_contact_person_rejects_invalid_fields(
    admin_client: httpx.AsyncClient,
) -> None:
    response = await admin_client.post(
        "/api/admin/contact-persons",
        json={
            **contact_payload(),
            "name": "   ",
            "email": "invalid-email",
        },
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_contact_person_requires_csrf(
    admin_client: httpx.AsyncClient,
) -> None:
    response = await admin_client.post(
        "/api/admin/contact-persons",
        json=contact_payload(),
        headers={
            "X-CSRF-Token": "",
        },
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_regular_employee_cannot_access_contact_persons(
    admin_client: httpx.AsyncClient,
    test_admin_session_factory: async_sessionmaker[AsyncSession],
    test_invitation,
) -> None:
    async with test_admin_session_factory() as db:
        employee = await db.get(
            Employee,
            test_invitation.employee_id,
        )

        assert employee is not None

        employee.role = "employee"

        await db.commit()

    get_response = await admin_client.get("/api/admin/contact-persons")

    post_response = await admin_client.post(
        "/api/admin/contact-persons",
        json=contact_payload(),
    )

    assert get_response.status_code == 403
    assert post_response.status_code == 403


@pytest.mark.asyncio
async def test_unauthenticated_user_cannot_access_contact_persons(
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
        ) as client:
            response = await client.get("/api/admin/contact-persons")

        assert response.status_code == 401

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_unknown_contact_returns_404(
    admin_client: httpx.AsyncClient,
) -> None:
    contact_id = uuid.uuid4()

    response = await admin_client.post(f"/api/admin/contact-persons/{contact_id}/deactivate")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_contact_persons_support_pagination(
    admin_client: httpx.AsyncClient,
    contact_cleanup: list[uuid.UUID],
) -> None:
    for index in range(3):
        response = await admin_client.post(
            "/api/admin/contact-persons",
            json=contact_payload(
                responsibility=f"Pagination-{uuid.uuid4().hex}",
            ),
        )

        assert response.status_code == 201

        contact_cleanup.append(uuid.UUID(response.json()["id"]))

    first_page = await admin_client.get(
        "/api/admin/contact-persons",
        params={
            "page": 1,
            "page_size": 2,
        },
    )

    assert first_page.status_code == 200

    first_data = first_page.json()

    assert first_data["page"] == 1
    assert first_data["page_size"] == 2
    assert len(first_data["items"]) == 2
    assert first_data["total_items"] >= 3
    assert first_data["total_pages"] >= 2

    second_page = await admin_client.get(
        "/api/admin/contact-persons",
        params={
            "page": 2,
            "page_size": 2,
        },
    )

    assert second_page.status_code == 200

    second_data = second_page.json()

    assert second_data["page"] == 2
    assert second_data["page_size"] == 2
    assert len(second_data["items"]) > 0

    first_ids = {contact["id"] for contact in first_data["items"]}

    second_ids = {contact["id"] for contact in second_data["items"]}

    assert first_ids.isdisjoint(second_ids)


@pytest.mark.asyncio
async def test_contact_persons_reject_invalid_pagination(
    admin_client: httpx.AsyncClient,
) -> None:
    invalid_page = await admin_client.get(
        "/api/admin/contact-persons",
        params={
            "page": 0,
        },
    )

    assert invalid_page.status_code == 422

    invalid_page_size = await admin_client.get(
        "/api/admin/contact-persons",
        params={
            "page_size": 101,
        },
    )

    assert invalid_page_size.status_code == 422
