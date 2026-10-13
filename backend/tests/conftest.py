import os
import uuid
from collections.abc import AsyncIterator
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from dotenv import load_dotenv
from sqlalchemy import delete, text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.models.employee import Employee
from app.models.employee_invitation import EmployeeInvitation

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

            if database_name != "neurolens_test":
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
            expires_at=(datetime.now(timezone.utc) + timedelta(days=7)),
        )

        session.add(employee)
        session.add(invitation)
        await session.commit()

    try:
        yield invitation

    finally:
        async with test_admin_session_factory() as session:
            await session.execute(delete(Employee).where(Employee.user_id == employee_id))
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
