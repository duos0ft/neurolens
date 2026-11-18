import uuid
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.email_outbox import EmailOutbox
from app.models.employee_invitation import EmployeeInvitation


class EmailOutboxService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def claim_delivery(
        self,
        outbox_id: uuid.UUID,
    ) -> EmailOutbox | None:
        now = datetime.now(timezone.utc)
        attempt_id = uuid.uuid4()

        ready_invitation = (
            select(EmployeeInvitation.id)
            .where(
                EmployeeInvitation.id == EmailOutbox.invitation_id,
                EmployeeInvitation.status == "ready",
                EmployeeInvitation.expires_at > now,
            )
            .exists()
        )

        statement = (
            update(EmailOutbox)
            .where(
                EmailOutbox.id == outbox_id,
                EmailOutbox.status == "pending",
                EmailOutbox.encrypted_token.is_not(None),
                ready_invitation,
            )
            .values(
                status="sending",
                delivery_attempt_id=attempt_id,
                delivery_started_at=now,
                attempt_count=EmailOutbox.attempt_count + 1,
                last_error_code=None,
            )
            .returning(EmailOutbox)
        )

        try:
            result = await self.db.execute(statement)
            outbox = result.scalar_one_or_none()

            if outbox is None:
                await self.db.rollback()
                return None

            await self.db.commit()
            return outbox

        except Exception:
            await self.db.rollback()
            raise

    async def complete_delivery(
        self,
        outbox_id: uuid.UUID,
        attempt_id: uuid.UUID,
        provider_message_id: str,
    ) -> bool:
        statement = (
            update(EmailOutbox)
            .where(
                EmailOutbox.id == outbox_id,
                EmailOutbox.status == "sending",
                EmailOutbox.delivery_attempt_id == attempt_id,
            )
            .values(
                status="sent",
                provider_message_id=provider_message_id,
                encrypted_token=None,
                delivery_attempt_id=None,
                delivery_started_at=None,
                last_error_code=None,
                sent_at=datetime.now(timezone.utc),
            )
            .returning(EmailOutbox.id)
        )

        try:
            result = await self.db.execute(statement)
            updated_id = result.scalar_one_or_none()

            if updated_id is None:
                await self.db.rollback()
                return False

            await self.db.commit()
            return True

        except Exception:
            await self.db.rollback()
            raise

    async def mark_reconciliation_required(
        self,
        outbox_id: uuid.UUID,
        attempt_id: uuid.UUID,
        error_code: str,
    ) -> bool:
        statement = (
            update(EmailOutbox)
            .where(
                EmailOutbox.id == outbox_id,
                EmailOutbox.status == "sending",
                EmailOutbox.delivery_attempt_id == attempt_id,
            )
            .values(
                status="reconciliation_required",
                delivery_attempt_id=None,
                delivery_started_at=None,
                last_error_code=error_code,
            )
            .returning(EmailOutbox.id)
        )

        try:
            result = await self.db.execute(statement)
            updated_id = result.scalar_one_or_none()

            if updated_id is None:
                await self.db.rollback()
                return False

            await self.db.commit()
            return True

        except Exception:
            await self.db.rollback()
            raise

    async def fail_delivery(
        self,
        outbox_id: uuid.UUID,
        attempt_id: uuid.UUID,
        error_code: str,
    ) -> bool:
        statement = (
            update(EmailOutbox)
            .where(
                EmailOutbox.id == outbox_id,
                EmailOutbox.status == "sending",
                EmailOutbox.delivery_attempt_id == attempt_id,
            )
            .values(
                status="failed",
                delivery_attempt_id=None,
                delivery_started_at=None,
                last_error_code=error_code,
            )
            .returning(EmailOutbox.id)
        )

        try:
            result = await self.db.execute(statement)
            updated_id = result.scalar_one_or_none()

            if updated_id is None:
                await self.db.rollback()
                return False

            await self.db.commit()
            return True

        except Exception:
            await self.db.rollback()
            raise
