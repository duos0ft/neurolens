import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.database import get_db
from app.core.permissions import require_admin
from app.main import create_app
from app.models.email_outbox import EmailOutbox
from app.models.employee import Employee
from app.models.employee_invitation import EmployeeInvitation
from app.models.employee_session import EmployeeSession
from app.services.authentication.oauth import generate_token, hash_token
from app.services.email.email_outbox import EmailOutboxService
from app.services.invitation.employee_invitation import EmployeeInvitationService


@pytest.mark.asyncio
async def test_suspending_employee_revokes_sessions(
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
        employee.provisioning_status = "completed"
        employee.auth0_user_id = f"email|{employee_id.hex}"

        employee_session = EmployeeSession(
            employee_id=employee_id,
            session_hash=hash_token(session_token),
            expires_at=now + timedelta(days=7),
        )

        db.add(employee_session)
        await db.commit()

        session_id = employee_session.id

    app = create_app()

    async def override_get_db():
        async with test_session_factory() as db:
            yield db

    # Provide a simulated administrator identity.
    # Authorization is bypassed only for this endpoint test.
    async def override_require_admin():
        return Employee(
            user_id=__import__("uuid").uuid4(),
            email="test-admin@example.com",
            role="admin",
            status="active",
            provisioning_status="completed",
        )

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[require_admin] = override_require_admin

    try:
        # Mock CSRF validation only, keeping endpoint logic intact.
        from unittest.mock import patch

        with (
            patch(
                "app.api.employees.validate_request_origin",
                return_value=None,
            ),
            patch(
                "fastapi_csrf_protect.CsrfProtect.validate_csrf",
                return_value=None,
            ),
        ):
            transport = httpx.ASGITransport(app=app)

            async with httpx.AsyncClient(
                transport=transport,
                base_url="http://testserver",
            ) as client:
                response = await client.post(
                    f"/api/employees/{employee_id}/suspend",
                    headers={
                        "Origin": "http://localhost:3000",
                    },
                )

        assert response.status_code == 204

        async with test_session_factory() as db:
            employee = await db.get(Employee, employee_id)
            stored_session = await db.get(EmployeeSession, session_id)

            assert employee is not None
            assert employee.status == "suspended"

            assert stored_session is not None
            assert stored_session.revoked_at is not None

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_reactivating_employee_does_not_restore_revoked_sessions(
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
        employee.provisioning_status = "completed"
        employee.auth0_user_id = f"email|{employee_id.hex}"

        employee_session = EmployeeSession(
            employee_id=employee_id,
            session_hash=hash_token(session_token),
            expires_at=now + timedelta(days=7),
            revoked_at=now - timedelta(minutes=1),
        )

        db.add(employee_session)
        await db.commit()

        session_id = employee_session.id

    app = create_app()

    async def override_get_db():
        async with test_session_factory() as db:
            yield db

    async def override_require_admin():
        return Employee(
            user_id=uuid.uuid4(),
            email="test-admin@example.com",
            role="admin",
            status="active",
            provisioning_status="completed",
        )

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[require_admin] = override_require_admin

    try:
        with patch(
            "fastapi_csrf_protect.CsrfProtect.validate_csrf",
            new_callable=AsyncMock,
        ):
            transport = httpx.ASGITransport(app=app)

            async with httpx.AsyncClient(
                transport=transport,
                base_url="http://testserver",
            ) as client:
                response = await client.post(
                    f"/api/employees/{employee_id}/reactivate",
                    headers={
                        "Origin": "http://localhost:3000",
                    },
                )

        assert response.status_code == 204

        async with test_session_factory() as db:
            employee = await db.get(Employee, employee_id)
            stored_session = await db.get(EmployeeSession, session_id)

            assert employee is not None
            assert employee.status == "active"

            assert stored_session is not None
            assert stored_session.revoked_at is not None

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_admin_cannot_suspend_themselves(
    test_session_factory: async_sessionmaker[AsyncSession],
    test_invitation,
    test_admin_session_factory,
) -> None:
    employee_id = test_invitation.employee_id

    async with test_admin_session_factory() as db:
        employee = await db.get(Employee, employee_id)

        assert employee is not None

        employee.role = "admin"
        employee.status = "active"
        employee.provisioning_status = "completed"
        employee.auth0_user_id = f"email|{employee_id.hex}"

        await db.commit()

    app = create_app()

    async def override_get_db():
        async with test_session_factory() as db:
            yield db

    async def override_require_admin():
        async with test_session_factory() as db:
            return await db.get(Employee, employee_id)

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[require_admin] = override_require_admin

    try:
        with patch(
            "fastapi_csrf_protect.CsrfProtect.validate_csrf",
            new_callable=AsyncMock,
        ):
            transport = httpx.ASGITransport(app=app)

            async with httpx.AsyncClient(
                transport=transport,
                base_url="http://testserver",
            ) as client:
                response = await client.post(
                    f"/api/employees/{employee_id}/suspend",
                    headers={"Origin": "http://localhost:3000"},
                )

        assert response.status_code == 403
        assert response.json()["detail"] == "You cannot suspend your own account"

        async with test_session_factory() as db:
            employee = await db.get(Employee, employee_id)

            assert employee is not None
            assert employee.status == "active"

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_cannot_suspend_last_active_administrator(
    test_session_factory: async_sessionmaker[AsyncSession],
    test_admin_session_factory: async_sessionmaker[AsyncSession],
    test_invitation,
) -> None:
    employee_id = test_invitation.employee_id

    # Prepare an active administrator using privileged test setup.
    async with test_admin_session_factory() as db:
        employee = await db.get(Employee, employee_id)

        assert employee is not None

        employee.role = "admin"
        employee.status = "active"
        employee.provisioning_status = "completed"
        employee.auth0_user_id = f"email|{employee_id.hex}"

        await db.commit()

    app = create_app()

    async def override_get_db():
        async with test_session_factory() as db:
            yield db

    # Another administrator performs the operation.
    async def override_require_admin():
        return Employee(
            user_id=uuid.uuid4(),
            email="another-admin@example.com",
            role="admin",
            status="active",
            provisioning_status="completed",
        )

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[require_admin] = override_require_admin

    try:
        with patch(
            "fastapi_csrf_protect.CsrfProtect.validate_csrf",
            new_callable=AsyncMock,
        ):
            transport = httpx.ASGITransport(app=app)

            async with httpx.AsyncClient(
                transport=transport,
                base_url="http://testserver",
            ) as client:
                response = await client.post(
                    f"/api/employees/{employee_id}/suspend",
                    headers={"Origin": "http://localhost:3000"},
                )

        assert response.status_code == 409
        assert response.json()["detail"] == ("The last active administrator cannot be suspended")

        async with test_session_factory() as db:
            employee = await db.get(Employee, employee_id)

            assert employee is not None
            assert employee.status == "active"

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_cancelled_invitation_cannot_be_accepted(
    test_session_factory: async_sessionmaker[AsyncSession],
    test_invitation: EmployeeInvitation,
) -> None:
    employee_id = test_invitation.employee_id
    invitation_id = test_invitation.id

    async with test_session_factory() as db:
        employee = await db.get(Employee, employee_id)
        invitation = await db.get(EmployeeInvitation, invitation_id)

        assert employee is not None
        assert invitation is not None

        employee.auth0_user_id = f"email|{employee_id.hex}"
        employee.provisioning_status = "completed"
        invitation.status = "ready"

        await db.commit()

    async with test_session_factory() as db:
        service = EmployeeInvitationService(db)

        cancelled = await service.cancel_invitation(employee_id)

        assert cancelled is True

    async with test_session_factory() as db:
        employee = await db.get(Employee, employee_id)
        invitation = await db.get(EmployeeInvitation, invitation_id)

        assert employee is not None
        assert employee.status == "invited"

        assert invitation is not None
        assert invitation.status == "cancelled"
        assert invitation.cancelled_at is not None

    # Repeated cancellation must not succeed.
    async with test_session_factory() as db:
        service = EmployeeInvitationService(db)

        cancelled_again = await service.cancel_invitation(employee_id)

        assert cancelled_again is False


@pytest.mark.asyncio
async def test_cancelled_invitation_fails_public_validation(
    test_session_factory: async_sessionmaker[AsyncSession],
    test_invitation: EmployeeInvitation,
) -> None:
    employee_id = test_invitation.employee_id
    invitation_token = generate_token()

    async with test_session_factory() as db:
        employee = await db.get(Employee, employee_id)
        invitation = await db.get(EmployeeInvitation, test_invitation.id)

        assert employee is not None
        assert invitation is not None

        employee.auth0_user_id = f"email|{employee_id.hex}"
        employee.provisioning_status = "completed"

        invitation.token_hash = hash_token(invitation_token)
        invitation.status = "ready"

        await db.commit()

    async with test_session_factory() as db:
        service = EmployeeInvitationService(db)
        assert await service.cancel_invitation(employee_id) is True

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
            response = await client.post(
                "/api/auth/invitations/validate",
                json={"token": invitation_token},
                headers={"Origin": "http://localhost:3000"},
            )

        assert response.status_code == 400
        assert response.json()["detail"] == ("This invitation is invalid or no longer available.")

        async with test_session_factory() as db:
            invitation = await db.get(
                EmployeeInvitation,
                test_invitation.id,
            )

            assert invitation is not None
            assert invitation.status == "cancelled"

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_cancelled_invitation_cannot_claim_email_delivery(
    test_session_factory: async_sessionmaker[AsyncSession],
    test_invitation: EmployeeInvitation,
) -> None:
    invitation_id = test_invitation.id

    async with test_session_factory() as db:
        invitation = await db.get(EmployeeInvitation, invitation_id)

        assert invitation is not None

        invitation.status = "cancelled"
        invitation.cancelled_at = datetime.now(timezone.utc)

        outbox = EmailOutbox(
            invitation_id=invitation_id,
            encrypted_token="test-encrypted-token",
            status="pending",
        )

        db.add(outbox)
        await db.commit()

        outbox_id = outbox.id

    async with test_session_factory() as db:
        service = EmailOutboxService(db)

        claimed = await service.claim_delivery(outbox_id)

        assert claimed is None

    async with test_session_factory() as db:
        outbox = await db.get(EmailOutbox, outbox_id)

        assert outbox is not None
        assert outbox.status == "pending"
        assert outbox.delivery_attempt_id is None
        assert outbox.delivery_started_at is None
        assert outbox.attempt_count == 0
