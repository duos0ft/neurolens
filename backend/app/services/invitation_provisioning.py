import uuid
from enum import StrEnum

from pydantic import BaseModel, model_validator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.employee_invitation import EmployeeInvitation
from app.schemas.auth0 import Auth0User
from app.schemas.auth0_errors import Auth0Operation
from app.schemas.invitation_provisioning import (
    ProvisioningResult,
    ProvisioningStatus,
)
from app.services.auth0_error_classifier import Auth0OperationError
from app.services.auth0_management import (
    Auth0IdentityConflictError,
    Auth0ManagementService,
)
from app.services.employee_invitation import EmployeeInvitationService


class IdentityReconciliationStatus(StrEnum):
    FOUND = "found"
    NOT_FOUND = "not_found"


class IdentityReconciliationResult(BaseModel):
    status: IdentityReconciliationStatus
    user: Auth0User | None = None

    @model_validator(mode="after")
    def validate_result(self) -> "IdentityReconciliationResult":
        if self.status == IdentityReconciliationStatus.FOUND:
            if self.user is None:
                raise ValueError("FOUND reconciliation result requires an Auth0 user")
        elif self.user is not None:
            raise ValueError("NOT_FOUND reconciliation result cannot contain a user")

        return self


class Auth0CreationReservationDeniedError(Exception):
    pass


class InvitationProvisioningCoordinator:
    def __init__(
        self,
        auth0: Auth0ManagementService,
        invitations: EmployeeInvitationService,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        self.auth0 = auth0
        self.invitations = invitations
        self.session_factory = session_factory

    @staticmethod
    def validate_identity(
        user: Auth0User,
        email: str,
        invitation_id: uuid.UUID,
    ) -> None:
        if user.email.casefold() != email.casefold():
            raise Auth0IdentityConflictError("Auth0 returned an unexpected email address")

        if not any(
            identity.provider == "email" and identity.connection == "email"
            for identity in user.identities
        ):
            raise Auth0IdentityConflictError("Auth0 returned an unexpected identity provider")

        if user.app_metadata.neurolens_invitation_id != str(invitation_id):
            raise Auth0IdentityConflictError("Auth0 invitation metadata does not match")

    async def reconcile_identity(
        self,
        email: str,
        invitation_id: uuid.UUID,
    ) -> IdentityReconciliationResult:
        user = await self.auth0.reconcile_invitation(
            email=email,
            invitation_id=invitation_id,
        )

        if user is None:
            return IdentityReconciliationResult(
                status=IdentityReconciliationStatus.NOT_FOUND,
            )

        self.validate_identity(
            user=user,
            email=email,
            invitation_id=invitation_id,
        )

        return IdentityReconciliationResult(
            status=IdentityReconciliationStatus.FOUND,
            user=user,
        )

    async def provision_new_identity(
        self,
        invitation: EmployeeInvitation,
        email: str,
    ) -> Auth0User:
        result = await self.reconcile_identity(
            email=email,
            invitation_id=invitation.id,
        )

        if result.status == IdentityReconciliationStatus.FOUND:
            if result.user is None:
                raise RuntimeError("Reconciliation returned FOUND without an Auth0 user")

            return result.user

        attempt_id = invitation.provisioning_attempt_id

        if attempt_id is None:
            raise RuntimeError("Invitation has no active provisioning attempt")

        access_token = await self.auth0.get_access_token()

        reserved = await self.invitations.reserve_auth0_creation(
            invitation_id=invitation.id,
            attempt_id=attempt_id,
        )

        if not reserved:
            raise Auth0CreationReservationDeniedError("Auth0 creation reservation was denied")

        user = await self.auth0.create_passwordless_user(
            email=email,
            invitation_id=invitation.id,
            access_token=access_token,
        )

        self.validate_identity(
            user=user,
            email=email,
            invitation_id=invitation.id,
        )

        return user

    async def _mark_reconciliation_required(
        self,
        invitation_id: uuid.UUID,
        attempt_id: uuid.UUID,
        error_code: str,
    ) -> ProvisioningResult:
        recorded = await self.invitations.mark_reconciliation_required(
            invitation_id=invitation_id,
            attempt_id=attempt_id,
            error_code=error_code,
        )

        return ProvisioningResult(
            status=(
                ProvisioningStatus.RECONCILIATION_REQUIRED
                if recorded
                else ProvisioningStatus.NOT_CLAIMED
            ),
            error_code=error_code,
        )

    async def provision_invitation(
        self,
        invitation_id: uuid.UUID,
    ) -> ProvisioningResult:
        invitation = await self.invitations.claim_invitation(invitation_id)

        if invitation is None:
            return ProvisioningResult(
                status=ProvisioningStatus.NOT_CLAIMED,
            )

        attempt_id = invitation.provisioning_attempt_id

        if attempt_id is None:
            raise RuntimeError("Claimed invitation has no provisioning attempt ID")

        try:
            email = await self.invitations.get_invited_employee_email(
                invitation.employee_id,
                self.session_factory,
            )

            user = await self.provision_new_identity(
                invitation=invitation,
                email=email,
            )

            completed = await self.invitations.complete_provisioning(
                invitation_id=invitation.id,
                attempt_id=attempt_id,
                auth0_user_id=user.user_id,
            )

            return ProvisioningResult(
                status=(
                    ProvisioningStatus.COMPLETED if completed else ProvisioningStatus.NOT_CLAIMED
                ),
            )

        except Auth0CreationReservationDeniedError:
            return ProvisioningResult(
                status=ProvisioningStatus.NOT_CLAIMED,
                error_code="auth0_creation_reservation_denied",
            )

        except Auth0OperationError as error:
            if error.result.operation == Auth0Operation.CREATE_USER:
                return await self._mark_reconciliation_required(
                    invitation_id=invitation.id,
                    attempt_id=attempt_id,
                    error_code=error.result.error_code,
                )

            recorded = await self.invitations.fail_provisioning(
                invitation_id=invitation.id,
                attempt_id=attempt_id,
                error_code=error.result.error_code,
            )

            return ProvisioningResult(
                status=(ProvisioningStatus.FAILED if recorded else ProvisioningStatus.NOT_CLAIMED),
                error_code=error.result.error_code,
            )

        except Auth0IdentityConflictError:
            # A conflict after creation was reserved must not
            # be treated as a confirmed pre-creation failure.
            recorded = await self.invitations.fail_provisioning(
                invitation_id=invitation.id,
                attempt_id=attempt_id,
                error_code="auth0_identity_conflict",
            )

            if recorded:
                return ProvisioningResult(
                    status=ProvisioningStatus.FAILED,
                    error_code="auth0_identity_conflict",
                )

            return await self._mark_reconciliation_required(
                invitation_id=invitation.id,
                attempt_id=attempt_id,
                error_code="auth0_identity_conflict",
            )

    async def recover_invitation(
        self,
        invitation_id: uuid.UUID,
    ) -> ProvisioningResult:
        invitation = await self.invitations.claim_reconciliation(invitation_id)

        if invitation is None:
            invitation = await self.invitations.claim_expired_provisioning(invitation_id)

        if invitation is None:
            return ProvisioningResult(
                status=ProvisioningStatus.NOT_CLAIMED,
            )

        attempt_id = invitation.provisioning_attempt_id

        if attempt_id is None:
            raise RuntimeError("Recovered invitation has no provisioning attempt ID")

        try:
            email = await self.invitations.get_invited_employee_email(
                invitation.employee_id,
                self.session_factory,
            )

            result = await self.reconcile_identity(
                email=email,
                invitation_id=invitation.id,
            )

            if result.status == IdentityReconciliationStatus.NOT_FOUND:
                return await self._mark_reconciliation_required(
                    invitation_id=invitation.id,
                    attempt_id=attempt_id,
                    error_code="auth0_identity_not_found",
                )

            if result.user is None:
                raise RuntimeError("Reconciliation returned FOUND without an Auth0 user")

            completed = await self.invitations.complete_provisioning(
                invitation_id=invitation.id,
                attempt_id=attempt_id,
                auth0_user_id=result.user.user_id,
            )

            return ProvisioningResult(
                status=(
                    ProvisioningStatus.COMPLETED if completed else ProvisioningStatus.NOT_CLAIMED
                ),
            )

        except Auth0OperationError as error:
            return await self._mark_reconciliation_required(
                invitation_id=invitation.id,
                attempt_id=attempt_id,
                error_code=error.result.error_code,
            )

        except Auth0IdentityConflictError:
            return await self._mark_reconciliation_required(
                invitation_id=invitation.id,
                attempt_id=attempt_id,
                error_code="auth0_identity_conflict",
            )

    async def recover_precreation(
        self,
        invitation_id: uuid.UUID,
    ) -> ProvisioningResult:
        invitation = await self.invitations.claim_expired_precreation(invitation_id)

        if invitation is None:
            return ProvisioningResult(
                status=ProvisioningStatus.NOT_CLAIMED,
            )

        attempt_id = invitation.provisioning_attempt_id

        if attempt_id is None:
            raise RuntimeError("Recovered invitation has no provisioning attempt ID")

        try:
            email = await self.invitations.get_invited_employee_email(
                invitation.employee_id,
                self.session_factory,
            )

            user = await self.provision_new_identity(
                invitation=invitation,
                email=email,
            )

            completed = await self.invitations.complete_provisioning(
                invitation_id=invitation.id,
                attempt_id=attempt_id,
                auth0_user_id=user.user_id,
            )

            return ProvisioningResult(
                status=(
                    ProvisioningStatus.COMPLETED if completed else ProvisioningStatus.NOT_CLAIMED
                ),
            )

        except Auth0CreationReservationDeniedError:
            return ProvisioningResult(
                status=ProvisioningStatus.NOT_CLAIMED,
                error_code="auth0_creation_reservation_denied",
            )

        except Auth0OperationError as error:
            if error.result.operation == Auth0Operation.CREATE_USER:
                return await self._mark_reconciliation_required(
                    invitation_id=invitation.id,
                    attempt_id=attempt_id,
                    error_code=error.result.error_code,
                )

            recorded = await self.invitations.fail_provisioning(
                invitation_id=invitation.id,
                attempt_id=attempt_id,
                error_code=error.result.error_code,
            )

            return ProvisioningResult(
                status=(ProvisioningStatus.FAILED if recorded else ProvisioningStatus.NOT_CLAIMED),
                error_code=error.result.error_code,
            )

        except Auth0IdentityConflictError:
            recorded = await self.invitations.fail_provisioning(
                invitation_id=invitation.id,
                attempt_id=attempt_id,
                error_code="auth0_identity_conflict",
            )

            if recorded:
                return ProvisioningResult(
                    status=ProvisioningStatus.FAILED,
                    error_code="auth0_identity_conflict",
                )

            return await self._mark_reconciliation_required(
                invitation_id=invitation.id,
                attempt_id=attempt_id,
                error_code="auth0_identity_conflict",
            )

