import secrets
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, or_, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.settings import settings
from app.models.email_outbox import EmailOutbox
from app.models.employee import Employee
from app.models.employee_invitation import EmployeeInvitation
from app.schemas.employee import EmployeeRole
from app.services.invitation_crypto import InvitationCryptoService
from app.services.oauth import hash_token


class EmployeeAlreadyExistsError(Exception):
    pass


class EmployeeInvitationService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_invitation(
        self,
        email: str,
        role: EmployeeRole = EmployeeRole.EMPLOYEE,
    ) -> Employee:
        normalized_email = email.strip().lower()

        existing_employee = await self.db.scalar(
            select(Employee).where(func.lower(Employee.email) == normalized_email)
        )

        if existing_employee is not None:
            await self.db.rollback()
            raise EmployeeAlreadyExistsError("An employee with this email already exists")

        invitation_token = secrets.token_urlsafe(32)

        employee = Employee(
            email=normalized_email,
            role=role.value,
            status="invited",
            provisioning_status="pending",
        )

        try:
            self.db.add(employee)
            await self.db.flush()

            invitation = EmployeeInvitation(
                employee_id=employee.user_id,
                token_hash=hash_token(invitation_token),
                status="pending",
                expires_at=(
                    datetime.now(timezone.utc) + timedelta(days=settings.invitation_lifetime_days)
                ),
            )

            self.db.add(invitation)
            await self.db.flush()

            crypto = InvitationCryptoService()

            outbox = EmailOutbox(
                invitation_id=invitation.id,
                encrypted_token=crypto.encrypt(
                    token=invitation_token,
                    invitation_id=str(invitation.id),
                ),
                status="pending",
            )

            self.db.add(outbox)
            await self.db.commit()

        except IntegrityError as error:
            await self.db.rollback()

            existing = await self.db.scalar(
                select(Employee.user_id).where(func.lower(Employee.email) == normalized_email)
            )
            await self.db.rollback()

            if existing is not None:
                raise EmployeeAlreadyExistsError(
                    "An employee with this email already exists"
                ) from error

            raise

        except Exception:
            await self.db.rollback()
            raise

        return employee

    async def claim_invitation(
        self,
        invitation_id: uuid.UUID,
    ) -> EmployeeInvitation | None:
        now = datetime.now(timezone.utc)
        attempt_id = uuid.uuid4()

        statement = (
            update(EmployeeInvitation)
            .where(
                EmployeeInvitation.id == invitation_id,
                EmployeeInvitation.status.in_(["pending", "failed"]),
                EmployeeInvitation.auth0_creation_started_at.is_(None),
                EmployeeInvitation.expires_at > now,
            )
            .values(
                status="provisioning",
                provisioning_started_at=now,
                provisioning_attempt_id=attempt_id,
                last_error_code=None,
                attempt_count=EmployeeInvitation.attempt_count + 1,
            )
            .returning(EmployeeInvitation)
        )

        result = await self.db.execute(statement)
        invitation = result.scalar_one_or_none()

        if invitation is None:
            await self.db.rollback()
            return None

        await self.db.commit()
        return invitation

    async def complete_provisioning(
        self,
        invitation_id: uuid.UUID,
        attempt_id: uuid.UUID,
        auth0_user_id: str,
    ) -> bool:
        statement = (
            update(EmployeeInvitation)
            .where(
                EmployeeInvitation.id == invitation_id,
                EmployeeInvitation.status == "provisioning",
                EmployeeInvitation.provisioning_attempt_id == attempt_id,
            )
            .values(
                status="ready",
                provisioning_started_at=None,
                provisioning_attempt_id=None,
                last_error_code=None,
            )
            .returning(EmployeeInvitation.employee_id)
        )

        result = await self.db.execute(statement)
        employee_id = result.scalar_one_or_none()

        if employee_id is None:
            await self.db.rollback()
            return False

        employee_result = await self.db.execute(
            update(Employee)
            .where(
                Employee.user_id == employee_id,
                Employee.status == "invited",
            )
            .values(
                auth0_user_id=auth0_user_id,
                provisioning_status="completed",
            )
        )

        if employee_result.rowcount != 1:
            await self.db.rollback()
            return False

        await self.db.commit()
        return True

    async def fail_provisioning(
        self,
        invitation_id: uuid.UUID,
        attempt_id: uuid.UUID,
        error_code: str,
    ) -> bool:
        statement = (
            update(EmployeeInvitation)
            .where(
                EmployeeInvitation.id == invitation_id,
                EmployeeInvitation.status == "provisioning",
                EmployeeInvitation.provisioning_attempt_id == attempt_id,
                EmployeeInvitation.auth0_creation_started_at.is_(None),
            )
            .values(
                status="failed",
                provisioning_started_at=None,
                provisioning_attempt_id=None,
                last_error_code=error_code,
            )
            .returning(EmployeeInvitation.employee_id)
        )

        result = await self.db.execute(statement)
        employee_id = result.scalar_one_or_none()

        if employee_id is None:
            await self.db.rollback()
            return False

        employee_result = await self.db.execute(
            update(Employee)
            .where(
                Employee.user_id == employee_id,
                Employee.status == "invited",
            )
            .values(
                provisioning_status="failed",
            )
        )

        if employee_result.rowcount != 1:
            await self.db.rollback()
            return False

        await self.db.commit()
        return True

    async def claim_expired_provisioning(
        self,
        invitation_id: uuid.UUID,
    ) -> EmployeeInvitation | None:
        now = datetime.now(timezone.utc)

        lease_cutoff = now - timedelta(seconds=settings.invitation_provisioning_lease_seconds)

        attempt_id = uuid.uuid4()

        statement = (
            update(EmployeeInvitation)
            .where(
                EmployeeInvitation.id == invitation_id,
                EmployeeInvitation.status == "provisioning",
                EmployeeInvitation.expires_at > now,
                or_(
                    EmployeeInvitation.provisioning_started_at <= lease_cutoff,
                    EmployeeInvitation.provisioning_started_at.is_(None),
                ),
            )
            .values(
                provisioning_started_at=now,
                provisioning_attempt_id=attempt_id,
                attempt_count=EmployeeInvitation.attempt_count + 1,
            )
            .returning(EmployeeInvitation)
        )

        result = await self.db.execute(statement)
        invitation = result.scalar_one_or_none()

        if invitation is None:
            await self.db.rollback()
            return None

        await self.db.commit()
        return invitation

    async def get_invited_employee_email(
        self,
        employee_id: uuid.UUID,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> str:
        async with session_factory() as session:
            email = await session.scalar(
                select(Employee.email).where(
                    Employee.user_id == employee_id,
                    Employee.status == "invited",
                )
            )

            if email is None:
                raise ValueError("Invitation has no valid invited employee")

            return email

    async def reserve_auth0_creation(
        self,
        invitation_id: uuid.UUID,
        attempt_id: uuid.UUID,
    ) -> bool:
        now = datetime.now(timezone.utc)

        statement = (
            update(EmployeeInvitation)
            .where(
                EmployeeInvitation.id == invitation_id,
                EmployeeInvitation.status == "provisioning",
                EmployeeInvitation.provisioning_attempt_id == attempt_id,
                EmployeeInvitation.auth0_creation_started_at.is_(None),
                EmployeeInvitation.expires_at > now,
            )
            .values(
                auth0_creation_started_at=now,
            )
            .returning(EmployeeInvitation.id)
        )

        result = await self.db.execute(statement)
        reserved_id = result.scalar_one_or_none()

        if reserved_id is None:
            await self.db.rollback()
            return False

        await self.db.commit()
        return True

    async def mark_reconciliation_required(
        self,
        invitation_id: uuid.UUID,
        attempt_id: uuid.UUID,
        error_code: str,
    ) -> bool:
        statement = (
            update(EmployeeInvitation)
            .where(
                EmployeeInvitation.id == invitation_id,
                EmployeeInvitation.status == "provisioning",
                EmployeeInvitation.provisioning_attempt_id == attempt_id,
                EmployeeInvitation.auth0_creation_started_at.is_not(None),
            )
            .values(
                status="reconciliation_required",
                provisioning_started_at=None,
                provisioning_attempt_id=None,
                last_error_code=error_code,
            )
            .returning(EmployeeInvitation.id)
        )

        result = await self.db.execute(statement)
        updated_id = result.scalar_one_or_none()

        if updated_id is None:
            await self.db.rollback()
            return False

        await self.db.commit()
        return True

    async def claim_reconciliation(
        self,
        invitation_id: uuid.UUID,
    ) -> EmployeeInvitation | None:
        now = datetime.now(timezone.utc)
        attempt_id = uuid.uuid4()

        statement = (
            update(EmployeeInvitation)
            .where(
                EmployeeInvitation.id == invitation_id,
                EmployeeInvitation.status == "reconciliation_required",
                EmployeeInvitation.auth0_creation_started_at.is_not(None),
                EmployeeInvitation.expires_at > now,
            )
            .values(
                status="provisioning",
                provisioning_attempt_id=attempt_id,
                provisioning_started_at=now,
                attempt_count=EmployeeInvitation.attempt_count + 1,
            )
            .returning(EmployeeInvitation)
        )

        result = await self.db.execute(statement)
        invitation = result.scalar_one_or_none()

        if invitation is None:
            await self.db.rollback()
            return None

        await self.db.commit()
        return invitation

    async def claim_expired_precreation(
        self,
        invitation_id: uuid.UUID,
    ) -> EmployeeInvitation | None:
        now = datetime.now(timezone.utc)

        lease_cutoff = now - timedelta(seconds=settings.invitation_provisioning_lease_seconds)

        attempt_id = uuid.uuid4()

        statement = (
            update(EmployeeInvitation)
            .where(
                EmployeeInvitation.id == invitation_id,
                EmployeeInvitation.status == "provisioning",
                EmployeeInvitation.auth0_creation_started_at.is_(None),
                EmployeeInvitation.expires_at > now,
                (
                    (EmployeeInvitation.provisioning_started_at <= lease_cutoff)
                    | EmployeeInvitation.provisioning_started_at.is_(None)
                ),
            )
            .values(
                provisioning_started_at=now,
                provisioning_attempt_id=attempt_id,
                attempt_count=EmployeeInvitation.attempt_count + 1,
                last_error_code=None,
            )
            .returning(EmployeeInvitation)
        )

        result = await self.db.execute(statement)
        invitation = result.scalar_one_or_none()

        if invitation is None:
            await self.db.rollback()
            return None

        await self.db.commit()
        return invitation

    async def cancel_invitation(
        self,
        employee_id: uuid.UUID,
    ) -> bool:
        now = datetime.now(timezone.utc)

        invitation = await self.db.scalar(
            select(EmployeeInvitation)
            .join(
                Employee,
                Employee.user_id == EmployeeInvitation.employee_id,
            )
            .where(
                EmployeeInvitation.employee_id == employee_id,
                Employee.status == "invited",
            )
            .with_for_update(of=EmployeeInvitation)
        )

        if invitation is None:
            await self.db.rollback()
            return False

        if invitation.status in ("accepted", "cancelled"):
            await self.db.rollback()
            return False

        # Do not cancel while an external Auth0 creation
        # operation may still be in progress.
        if invitation.status in (
            "provisioning",
            "reconciliation_required",
        ):
            await self.db.rollback()
            return False

        invitation.status = "cancelled"
        invitation.cancelled_at = now

        await self.db.commit()

        return True

    @staticmethod
    def is_provisioning_lease_expired(
        invitation: EmployeeInvitation,
    ) -> bool:
        if invitation.status != "provisioning":
            return False

        if invitation.provisioning_started_at is None:
            return True

        expires_at = invitation.provisioning_started_at + timedelta(
            seconds=settings.invitation_provisioning_lease_seconds
        )

        return datetime.now(timezone.utc) >= expires_at
