import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.email_outbox import EmailOutbox
from app.models.employee import Employee
from app.models.employee_invitation import EmployeeInvitation
from app.services.email_outbox import EmailOutboxService
from app.services.invitation_crypto import InvitationCryptoService
from app.services.invitation_email import InvitationEmailService
from app.services.resend import ResendAPIError, ResendService


class EmailDeliveryNotReadyError(Exception):
    pass


class EmailDeliveryCoordinator:
    def __init__(
        self,
        resend: ResendService,
        outbox: EmailOutboxService,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        self.resend = resend
        self.outbox = outbox
        self.session_factory = session_factory
        self.crypto = InvitationCryptoService()

    async def get_delivery_details(
        self,
        outbox_id: uuid.UUID,
        attempt_id: uuid.UUID,
    ) -> tuple[str, str, uuid.UUID]:
        async with self.session_factory() as session:
            result = await session.execute(
                select(
                    Employee.email,
                    EmailOutbox.encrypted_token,
                    EmployeeInvitation.id,
                )
                .join(
                    EmployeeInvitation,
                    EmailOutbox.invitation_id == EmployeeInvitation.id,
                )
                .join(
                    Employee,
                    EmployeeInvitation.employee_id == Employee.user_id,
                )
                .where(
                    EmailOutbox.id == outbox_id,
                    EmailOutbox.status == "sending",
                    EmailOutbox.delivery_attempt_id == attempt_id,
                    EmployeeInvitation.status == "ready",
                    EmployeeInvitation.expires_at > datetime.now(timezone.utc),
                )
            )

            row = result.one_or_none()

            if row is None:
                raise EmailDeliveryNotReadyError("Email delivery is not ready")

            recipient, encrypted_token, invitation_id = row

            if recipient is None or encrypted_token is None:
                raise ValueError("Email delivery data is incomplete")

            return recipient, encrypted_token, invitation_id

    async def deliver_invitation(
        self,
        outbox_id: uuid.UUID,
    ) -> bool:
        claimed = await self.outbox.claim_delivery(outbox_id)

        if claimed is None:
            return False

        attempt_id = claimed.delivery_attempt_id

        if attempt_id is None:
            raise RuntimeError("Claimed delivery has no attempt ID")

        try:
            recipient, encrypted_token, invitation_id = await self.get_delivery_details(
                outbox_id=outbox_id,
                attempt_id=attempt_id,
            )

            token = self.crypto.decrypt(
                encrypted_token=encrypted_token,
                invitation_id=str(invitation_id),
            )

            email_request = InvitationEmailService.build_email(
                recipient=recipient,
                token=token,
            )

        except EmailDeliveryNotReadyError:
            await self.outbox.fail_delivery(
                outbox_id=outbox_id,
                attempt_id=attempt_id,
                error_code="invitation_not_ready",
            )
            return False

        except Exception:
            # No Resend request was attempted.
            await self.outbox.fail_delivery(
                outbox_id=outbox_id,
                attempt_id=attempt_id,
                error_code="email_preparation_failed",
            )
            raise

        try:
            response = await self.resend.send_email(
                request=email_request,
                idempotency_key=str(outbox_id),
            )

        except ResendAPIError as error:
            error_code = (
                f"resend_http_{error.status_code}"
                if error.status_code is not None
                else "resend_transport_error"
            )

            # The delivery outcome may be uncertain.
            await self.outbox.mark_reconciliation_required(
                outbox_id=outbox_id,
                attempt_id=attempt_id,
                error_code=error_code,
            )

            return False

        return await self.outbox.complete_delivery(
            outbox_id=outbox_id,
            attempt_id=attempt_id,
            provider_message_id=response.id,
        )
