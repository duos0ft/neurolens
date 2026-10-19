import asyncio
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.employee import Employee
from app.models.employee_invitation import EmployeeInvitation
from app.services.employee_invitation import EmployeeInvitationService


@pytest.mark.asyncio
async def test_only_one_worker_can_claim_invitation(
    test_session_factory: async_sessionmaker[AsyncSession],
    test_invitation: EmployeeInvitation,
) -> None:
    invitation_id = test_invitation.id

    async def claim() -> EmployeeInvitation | None:
        async with test_session_factory() as session:
            service = EmployeeInvitationService(session)
            return await service.claim_invitation(invitation_id)

    first, second = await asyncio.gather(
        claim(),
        claim(),
    )

    successful_claims = [result for result in (first, second) if result is not None]

    assert len(successful_claims) == 1

    async with test_session_factory() as session:
        invitation = await session.scalar(
            select(EmployeeInvitation).where(EmployeeInvitation.id == invitation_id)
        )

        assert invitation is not None
        assert invitation.status == "provisioning"
        assert invitation.attempt_count == 1
        assert invitation.provisioning_attempt_id is not None


@pytest.mark.asyncio
async def test_only_one_worker_can_reserve_auth0_creation(
    test_session_factory: async_sessionmaker[AsyncSession],
    test_invitation: EmployeeInvitation,
) -> None:
    invitation_id = test_invitation.id

    async with test_session_factory() as session:
        service = EmployeeInvitationService(session)
        claimed = await service.claim_invitation(invitation_id)

    assert claimed is not None
    assert claimed.provisioning_attempt_id is not None

    attempt_id = claimed.provisioning_attempt_id

    async def reserve() -> bool:
        async with test_session_factory() as session:
            service = EmployeeInvitationService(session)

            return await service.reserve_auth0_creation(
                invitation_id=invitation_id,
                attempt_id=attempt_id,
            )

    first, second = await asyncio.gather(
        reserve(),
        reserve(),
    )

    assert sorted([first, second]) == [False, True]

    async with test_session_factory() as session:
        invitation = await session.scalar(
            select(EmployeeInvitation).where(EmployeeInvitation.id == invitation_id)
        )

        assert invitation is not None
        assert invitation.status == "provisioning"
        assert invitation.provisioning_attempt_id == attempt_id
        assert invitation.auth0_creation_started_at is not None
        assert invitation.attempt_count == 1


@pytest.mark.asyncio
async def test_stale_worker_cannot_complete_provisioning(
    test_session_factory: async_sessionmaker[AsyncSession],
    test_invitation: EmployeeInvitation,
) -> None:
    invitation_id = test_invitation.id

    # Worker A claims the invitation.
    async with test_session_factory() as session:
        service = EmployeeInvitationService(session)
        first_claim = await service.claim_invitation(invitation_id)

    assert first_claim is not None
    assert first_claim.provisioning_attempt_id is not None

    first_attempt_id = first_claim.provisioning_attempt_id

    # Simulate an expired provisioning lease.
    expired_at = datetime.now(timezone.utc) - timedelta(hours=1)

    async with test_session_factory() as session:
        await session.execute(
            update(EmployeeInvitation)
            .where(EmployeeInvitation.id == invitation_id)
            .values(
                provisioning_started_at=expired_at,
                auth0_creation_started_at=expired_at,
            )
        )
        await session.commit()

    # Worker B takes ownership.
    async with test_session_factory() as session:
        service = EmployeeInvitationService(session)
        second_claim = await service.claim_expired_provisioning(invitation_id)

    assert second_claim is not None
    assert second_claim.provisioning_attempt_id is not None

    second_attempt_id = second_claim.provisioning_attempt_id

    assert first_attempt_id != second_attempt_id

    # Worker A tries to complete using its old attempt ID.
    async with test_session_factory() as session:
        service = EmployeeInvitationService(session)

        completed = await service.complete_provisioning(
            invitation_id=invitation_id,
            attempt_id=first_attempt_id,
            auth0_user_id="email|stale-worker",
        )

    assert completed is False

    # The invitation must still belong to Worker B.
    async with test_session_factory() as session:
        invitation = await session.scalar(
            select(EmployeeInvitation).where(EmployeeInvitation.id == invitation_id)
        )

        assert invitation is not None
        assert invitation.status == "provisioning"
        assert invitation.provisioning_attempt_id == second_attempt_id
        assert invitation.attempt_count == 2


@pytest.mark.asyncio
async def test_reconciliation_recovers_existing_auth0_identity(
    test_session_factory: async_sessionmaker[AsyncSession],
    test_invitation: EmployeeInvitation,
) -> None:
    invitation_id = test_invitation.id
    auth0_user_id = "email|recovered-user"

    # Claim the invitation.
    async with test_session_factory() as session:
        service = EmployeeInvitationService(session)
        claimed = await service.claim_invitation(invitation_id)

    assert claimed is not None
    assert claimed.provisioning_attempt_id is not None

    attempt_id = claimed.provisioning_attempt_id

    # Simulate a successfully reserved Auth0 creation request.
    async with test_session_factory() as session:
        service = EmployeeInvitationService(session)

        reserved = await service.reserve_auth0_creation(
            invitation_id=invitation_id,
            attempt_id=attempt_id,
        )

    assert reserved is True

    # Simulate an Auth0 timeout and uncertain creation outcome.
    async with test_session_factory() as session:
        service = EmployeeInvitationService(session)

        marked = await service.mark_reconciliation_required(
            invitation_id=invitation_id,
            attempt_id=attempt_id,
            error_code="auth0_transport_error",
        )

    assert marked is True

    # A recovery worker claims the invitation.
    async with test_session_factory() as session:
        service = EmployeeInvitationService(session)

        recovered = await service.claim_reconciliation(invitation_id)

    assert recovered is not None
    assert recovered.provisioning_attempt_id is not None
    assert recovered.provisioning_attempt_id != attempt_id

    # The recovery worker reconciles the existing Auth0 user
    # and completes provisioning.
    async with test_session_factory() as session:
        service = EmployeeInvitationService(session)

        completed = await service.complete_provisioning(
            invitation_id=invitation_id,
            attempt_id=recovered.provisioning_attempt_id,
            auth0_user_id=auth0_user_id,
        )

    assert completed is True

    # Verify the committed invitation state.
    async with test_session_factory() as session:
        invitation = await session.scalar(
            select(EmployeeInvitation).where(EmployeeInvitation.id == invitation_id)
        )

        employee = await session.scalar(
            select(Employee).where(Employee.user_id == invitation.employee_id)
        )

        assert invitation.status == "ready"
        assert invitation.provisioning_attempt_id is None
        assert invitation.provisioning_started_at is None
        assert invitation.auth0_creation_started_at is not None

        assert employee is not None
        assert employee.auth0_user_id == auth0_user_id
        assert employee.provisioning_status == "completed"
        assert employee.status == "invited"
