from datetime import datetime, timedelta, timezone

import httpx
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.database import get_db
from app.main import create_app
from app.models.employee import Employee
from app.models.employee_session import EmployeeSession
from app.services.authentication.oauth import generate_token, hash_token


@pytest.mark.asyncio
async def test_inactive_session_is_rejected(
    test_session_factory: async_sessionmaker[AsyncSession],
    test_invitation,
) -> None:
    employee_id = test_invitation.employee_id
    session_token = generate_token()
    now = datetime.now(timezone.utc)

    async with test_session_factory() as db:
        employee = await db.get(Employee, employee_id)

        assert employee is not None

        employee.status = "active"

        session = EmployeeSession(
            employee_id=employee_id,
            session_hash=hash_token(session_token),
            last_active_at=now - timedelta(hours=13),
            expires_at=now + timedelta(days=7),
        )

        db.add(session)
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
            base_url="http://testserver",
        ) as client:
            client.cookies.set(
                "neurolens_session",
                session_token,
                path="/",
            )

            response = await client.get("/api/auth/me")

        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid or expired session"

        async with test_session_factory() as db:
            stored_session = await db.scalar(
                select(EmployeeSession).where(
                    EmployeeSession.session_hash == hash_token(session_token),
                )
            )

            assert stored_session is not None
            assert stored_session.revoked_at is None
            assert stored_session.last_active_at < (
                datetime.now(timezone.utc) - timedelta(hours=12)
            )

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_auth_me_does_not_update_last_activity(
    test_session_factory: async_sessionmaker[AsyncSession],
    test_invitation,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    employee_id = test_invitation.employee_id
    session_token = generate_token()
    now = datetime.now(timezone.utc)

    original_activity = now - timedelta(minutes=10)
    absolute_expiration = now + timedelta(days=7)

    async with test_session_factory() as db:
        employee = await db.get(Employee, employee_id)

        assert employee is not None

        employee.status = "active"

        session = EmployeeSession(
            employee_id=employee_id,
            session_hash=hash_token(session_token),
            last_active_at=original_activity,
            expires_at=absolute_expiration,
        )

        db.add(session)
        await db.commit()

        session_id = session.id

    # Ensure any unexpected activity update uses the test database.
    monkeypatch.setattr(
        "app.core.auth.async_session_factory",
        test_session_factory,
    )

    app = create_app()

    async def override_get_db():
        async with test_session_factory() as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db

    try:
        transport = httpx.ASGITransport(app=app)

        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://testserver",
        ) as client:
            client.cookies.set(
                "neurolens_session",
                session_token,
                path="/",
            )

            response = await client.get("/api/auth/me")

        assert response.status_code == 200

        async with test_session_factory() as db:
            stored_session = await db.get(EmployeeSession, session_id)

            assert stored_session is not None

            # Reading the current employee must not refresh activity.
            assert stored_session.last_active_at == original_activity

            # The absolute session lifetime must remain unchanged.
            assert stored_session.expires_at == absolute_expiration

            assert stored_session.revoked_at is None

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_recently_active_session_does_not_update_activity(
    test_session_factory: async_sessionmaker[AsyncSession],
    test_invitation,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    employee_id = test_invitation.employee_id
    session_token = generate_token()
    now = datetime.now(timezone.utc)

    original_activity = now - timedelta(minutes=2)
    absolute_expiration = now + timedelta(days=7)

    async with test_session_factory() as db:
        employee = await db.get(Employee, employee_id)

        assert employee is not None

        employee.status = "active"

        session = EmployeeSession(
            employee_id=employee_id,
            session_hash=hash_token(session_token),
            last_active_at=original_activity,
            expires_at=absolute_expiration,
        )

        db.add(session)
        await db.commit()

        session_id = session.id

    # Ensure an unexpected activity update would use the test database.
    monkeypatch.setattr(
        "app.core.auth.async_session_factory",
        test_session_factory,
    )

    app = create_app()

    async def override_get_db():
        async with test_session_factory() as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db

    try:
        transport = httpx.ASGITransport(app=app)

        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://testserver",
        ) as client:
            client.cookies.set(
                "neurolens_session",
                session_token,
                path="/",
            )

            response = await client.get("/api/auth/me")

        assert response.status_code == 200

        async with test_session_factory() as db:
            stored_session = await db.get(EmployeeSession, session_id)

            assert stored_session is not None

            # Less than five minutes have passed:
            # no activity timestamp update should occur.
            assert stored_session.last_active_at == original_activity

            # Absolute expiration must remain unchanged.
            assert stored_session.expires_at == absolute_expiration

            assert stored_session.revoked_at is None

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_revoked_session_is_rejected(
    test_session_factory: async_sessionmaker[AsyncSession],
    test_invitation,
) -> None:
    employee_id = test_invitation.employee_id
    session_token = generate_token()
    now = datetime.now(timezone.utc)

    async with test_session_factory() as db:
        employee = await db.get(Employee, employee_id)

        assert employee is not None

        employee.status = "active"

        session = EmployeeSession(
            employee_id=employee_id,
            session_hash=hash_token(session_token),
            last_active_at=now - timedelta(minutes=2),
            expires_at=now + timedelta(days=7),
            revoked_at=now - timedelta(seconds=30),
        )

        db.add(session)
        await db.commit()

        session_id = session.id

    app = create_app()

    async def override_get_db():
        async with test_session_factory() as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db

    try:
        transport = httpx.ASGITransport(app=app)

        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://testserver",
        ) as client:
            client.cookies.set(
                "neurolens_session",
                session_token,
                path="/",
            )

            response = await client.get("/api/auth/me")

        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid or expired session"

        async with test_session_factory() as db:
            stored_session = await db.get(EmployeeSession, session_id)

            assert stored_session is not None
            assert stored_session.revoked_at is not None
            assert stored_session.last_active_at == (now - timedelta(minutes=2))

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_suspended_employee_cannot_use_existing_session(
    test_session_factory: async_sessionmaker[AsyncSession],
    test_invitation,
) -> None:
    employee_id = test_invitation.employee_id
    session_token = generate_token()
    now = datetime.now(timezone.utc)

    async with test_session_factory() as db:
        employee = await db.get(Employee, employee_id)

        assert employee is not None

        employee.status = "suspended"

        session = EmployeeSession(
            employee_id=employee_id,
            session_hash=hash_token(session_token),
            last_active_at=now - timedelta(minutes=2),
            expires_at=now + timedelta(days=7),
        )

        db.add(session)
        await db.commit()

        session_id = session.id

    app = create_app()

    async def override_get_db():
        async with test_session_factory() as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db

    try:
        transport = httpx.ASGITransport(app=app)

        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://testserver",
        ) as client:
            client.cookies.set(
                "neurolens_session",
                session_token,
                path="/",
            )

            response = await client.get("/api/auth/me")

        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid or expired session"

        async with test_session_factory() as db:
            employee = await db.get(Employee, employee_id)
            stored_session = await db.get(EmployeeSession, session_id)

            assert employee is not None
            assert employee.status == "suspended"

            assert stored_session is not None
            assert stored_session.revoked_at is None
            assert stored_session.last_active_at == (now - timedelta(minutes=2))

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_session_is_rejected_after_absolute_expiration(
    test_session_factory: async_sessionmaker[AsyncSession],
    test_invitation,
) -> None:
    employee_id = test_invitation.employee_id
    session_token = generate_token()
    now = datetime.now(timezone.utc)

    async with test_session_factory() as db:
        employee = await db.get(Employee, employee_id)

        assert employee is not None

        employee.status = "active"

        session = EmployeeSession(
            employee_id=employee_id,
            session_hash=hash_token(session_token),
            created_at=now - timedelta(days=8),
            last_active_at=now - timedelta(minutes=2),
            expires_at=now - timedelta(days=1),
        )

        db.add(session)
        await db.commit()

        session_id = session.id

    app = create_app()

    async def override_get_db():
        async with test_session_factory() as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db

    try:
        transport = httpx.ASGITransport(app=app)

        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://testserver",
        ) as client:
            client.cookies.set(
                "neurolens_session",
                session_token,
                path="/",
            )

            response = await client.get("/api/auth/me")

        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid or expired session"

        async with test_session_factory() as db:
            stored_session = await db.get(EmployeeSession, session_id)

            assert stored_session is not None
            assert stored_session.expires_at < now
            assert stored_session.revoked_at is None

            # Recent activity cannot bypass absolute expiration.
            assert stored_session.last_active_at > (now - timedelta(hours=12))

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_old_session_rejected_even_with_future_expiration(
    test_session_factory: async_sessionmaker[AsyncSession],
    test_invitation,
) -> None:
    employee_id = test_invitation.employee_id
    session_token = generate_token()
    now = datetime.now(timezone.utc)

    async with test_session_factory() as db:
        employee = await db.get(Employee, employee_id)

        assert employee is not None

        employee.status = "active"

        session = EmployeeSession(
            employee_id=employee_id,
            session_hash=hash_token(session_token),
            created_at=now - timedelta(days=8),
            last_active_at=now - timedelta(minutes=2),
            expires_at=now + timedelta(days=1),
        )

        db.add(session)
        await db.commit()

        session_id = session.id

    app = create_app()

    async def override_get_db():
        async with test_session_factory() as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db

    try:
        transport = httpx.ASGITransport(app=app)

        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://testserver",
        ) as client:
            client.cookies.set(
                "neurolens_session",
                session_token,
                path="/",
            )

            response = await client.get("/api/auth/me")

        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid or expired session"

        async with test_session_factory() as db:
            stored_session = await db.get(EmployeeSession, session_id)

            assert stored_session is not None
            assert stored_session.created_at < now - timedelta(days=7)
            assert stored_session.expires_at > now
            assert stored_session.last_active_at > now - timedelta(hours=12)

    finally:
        app.dependency_overrides.clear()
