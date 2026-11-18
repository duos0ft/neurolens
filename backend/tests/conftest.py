import os
import uuid
from collections.abc import AsyncIterator
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx
import pytest
from dotenv import load_dotenv
from fastapi_csrf_protect import CsrfProtect
from sqlalchemy import delete, text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.api.assistant_dependencies import get_ai_provider_registry
from app.core.database import get_db, get_session_factory
from app.core.settings import settings
from app.main import create_app
from app.models.employee import Employee
from app.models.employee_invitation import EmployeeInvitation
from app.models.employee_session import EmployeeSession
from app.services.authentication.oauth import generate_token, hash_token

load_dotenv(
    dotenv_path=Path(__file__).resolve().parents[1] / ".env",
    override=False,
)


@pytest.fixture(scope="session")
def test_database_url() -> str:
    database_url = os.environ.get("TEST_DATABASE_URL")

    if not database_url:
        raise RuntimeError("TEST_DATABASE_URL must be configured")

    return database_url


@pytest.fixture
async def test_session_factory(
    test_database_url: str,
) -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    engine = create_async_engine(
        test_database_url,
        pool_pre_ping=True,
    )

    try:
        async with engine.connect() as connection:
            database_name = await connection.scalar(text("SELECT current_database()"))

            if database_name not in {"neurolens_test", "neurolens"}:
                raise RuntimeError("Integration tests cannot run against a non-test database")

        yield async_sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    finally:
        await engine.dispose()


@pytest.fixture
async def test_invitation(
    test_session_factory: async_sessionmaker[AsyncSession],
    test_admin_session_factory: async_sessionmaker[AsyncSession],
) -> AsyncIterator[EmployeeInvitation]:
    employee_id = uuid.uuid4()
    invitation_id = uuid.uuid4()

    async with test_session_factory() as session:
        employee = Employee(
            user_id=employee_id,
            email=f"test-{employee_id.hex}@example.com",
            role="employee",
            status="invited",
            provisioning_status="pending",
        )

        invitation = EmployeeInvitation(
            id=invitation_id,
            employee_id=employee_id,
            token_hash=uuid.uuid4().hex,
            status="pending",
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )

        session.add(employee)
        session.add(invitation)

        await session.commit()

    try:
        yield invitation

    finally:
        async with test_admin_session_factory() as session:
            await session.execute(
                delete(Employee).where(
                    Employee.user_id == employee_id,
                )
            )

            await session.commit()


@pytest.fixture
async def test_admin_session_factory(
    test_session_factory: async_sessionmaker[AsyncSession],
) -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    database_url = os.environ.get("TEST_MIGRATION_DATABASE_URL")

    if not database_url:
        raise RuntimeError("TEST_MIGRATION_DATABASE_URL must be configured")

    engine = create_async_engine(
        database_url,
        pool_pre_ping=True,
    )

    try:
        yield async_sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    finally:
        await engine.dispose()


@pytest.fixture
async def admin_client(
    test_session_factory: async_sessionmaker[AsyncSession],
    test_admin_session_factory: async_sessionmaker[AsyncSession],
    test_invitation,
) -> AsyncIterator[httpx.AsyncClient]:
    employee_id = test_invitation.employee_id
    session_token = generate_token()
    now = datetime.now(timezone.utc)

    async with test_admin_session_factory() as db:
        employee = await db.get(Employee, employee_id)

        assert employee is not None

        employee.role = "admin"
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
    app.dependency_overrides[get_session_factory] = lambda: test_session_factory

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

            yield client

    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def mock_ai_registry():
    from tests.helpers.mock_ai_registry import create_mock_ai_registry

    return create_mock_ai_registry()


@pytest.fixture
async def employee_client(
    test_session_factory: async_sessionmaker[AsyncSession],
    test_admin_session_factory: async_sessionmaker[AsyncSession],
    test_invitation: EmployeeInvitation,
    mock_ai_registry,
) -> AsyncIterator[httpx.AsyncClient]:
    employee_id = test_invitation.employee_id
    session_token = generate_token()
    now = datetime.now(timezone.utc)

    async with test_admin_session_factory() as db:
        employee = await db.get(Employee, employee_id)

        assert employee is not None

        employee.role = "employee"
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

    registry, _ = mock_ai_registry

    app.dependency_overrides[get_ai_provider_registry] = lambda: registry

    async def override_get_db():
        async with test_session_factory() as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_session_factory] = lambda: test_session_factory

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

            yield client

    finally:
        app.dependency_overrides.clear()
