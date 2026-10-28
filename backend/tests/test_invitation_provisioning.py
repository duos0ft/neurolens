from unittest.mock import AsyncMock

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.employee import Employee
from app.models.employee_invitation import EmployeeInvitation
from app.schemas.auth0 import (
    Auth0AppMetadata,
    Auth0Identity,
    Auth0User,
)
from app.schemas.auth0_errors import (
    Auth0ErrorCategory,
    Auth0ErrorResult,
    Auth0Operation,
)
from app.schemas.invitation_provisioning import ProvisioningStatus
from app.services.auth0_error_classifier import Auth0OperationError
from app.services.employee_invitation import EmployeeInvitationService
from app.services.invitation_provisioning import (
    InvitationProvisioningCoordinator,
)


@pytest.mark.asyncio
async def test_auth0_timeout_recovers_without_duplicate_creation(
    test_session_factory: async_sessionmaker[AsyncSession],
    test_invitation: EmployeeInvitation,
) -> None:
    invitation_id = test_invitation.id
    employee_id = test_invitation.employee_id

    async with test_session_factory() as session:
        email = await session.scalar(select(Employee.email).where(Employee.user_id == employee_id))

    assert email is not None

    auth0_user = Auth0User(
        user_id="email|recovered-user",
        email=email,
        identities=[
            Auth0Identity(
                provider="email",
                connection="email",
                user_id="recovered-user",
            )
        ],
        app_metadata=Auth0AppMetadata(
            neurolens_invitation_id=str(invitation_id),
        ),
    )

    auth0 = AsyncMock()

    auth0.get_access_token.return_value = "test-access-token"

    auth0.reconcile_invitation.side_effect = [
        None,
        auth0_user,
    ]

    auth0.create_passwordless_user.side_effect = Auth0OperationError(
        Auth0ErrorResult(
            operation=Auth0Operation.CREATE_USER,
            category=Auth0ErrorCategory.UNCERTAIN,
            error_code="auth0_transport_error",
        )
    )

    async with test_session_factory() as session:
        coordinator = InvitationProvisioningCoordinator(
            auth0=auth0,
            invitations=EmployeeInvitationService(session),
            session_factory=test_session_factory,
        )

        first_result = await coordinator.provision_invitation(invitation_id)

        assert first_result.status == ProvisioningStatus.RECONCILIATION_REQUIRED

        recovery_result = await coordinator.recover_invitation(invitation_id)

        assert recovery_result.status == ProvisioningStatus.COMPLETED

    auth0.create_passwordless_user.assert_awaited_once_with(
        email=email,
        invitation_id=invitation_id,
        access_token="test-access-token",
    )

    assert auth0.reconcile_invitation.await_count == 2

    async with test_session_factory() as session:
        invitation = await session.scalar(
            select(EmployeeInvitation).where(EmployeeInvitation.id == invitation_id)
        )

        employee = await session.scalar(select(Employee).where(Employee.user_id == employee_id))

        assert invitation is not None
        assert employee is not None

        assert invitation.status == "ready"
        assert invitation.provisioning_attempt_id is None
        assert invitation.auth0_creation_started_at is not None

        assert employee.auth0_user_id == auth0_user.user_id
        assert employee.provisioning_status == "completed"
        assert employee.status == "invited"


@pytest.mark.asyncio
async def test_auth0_recovery_keeps_unresolved_invitation(
    test_session_factory: async_sessionmaker[AsyncSession],
    test_invitation: EmployeeInvitation,
) -> None:
    invitation_id = test_invitation.id
    employee_id = test_invitation.employee_id

    auth0 = AsyncMock()
    auth0.get_access_token.return_value = "test-access-token"
    auth0.reconcile_invitation.return_value = None

    auth0.create_passwordless_user.side_effect = Auth0OperationError(
        Auth0ErrorResult(
            operation=Auth0Operation.CREATE_USER,
            category=Auth0ErrorCategory.UNCERTAIN,
            error_code="auth0_transport_error",
        )
    )

    async with test_session_factory() as session:
        coordinator = InvitationProvisioningCoordinator(
            auth0=auth0,
            invitations=EmployeeInvitationService(session),
            session_factory=test_session_factory,
        )

        first_result = await coordinator.provision_invitation(invitation_id)

        assert first_result.status == ProvisioningStatus.RECONCILIATION_REQUIRED

        recovery_result = await coordinator.recover_invitation(invitation_id)

        assert recovery_result.status == ProvisioningStatus.RECONCILIATION_REQUIRED

    auth0.create_passwordless_user.assert_awaited_once()
    assert auth0.reconcile_invitation.await_count == 2

    async with test_session_factory() as session:
        invitation = await session.scalar(
            select(EmployeeInvitation).where(EmployeeInvitation.id == invitation_id)
        )

        employee = await session.scalar(select(Employee).where(Employee.user_id == employee_id))

        assert invitation is not None
        assert employee is not None

        assert invitation.status == "reconciliation_required"
        assert invitation.provisioning_attempt_id is None
        assert invitation.auth0_creation_started_at is not None

        assert employee.status == "invited"
        assert employee.auth0_user_id is None
