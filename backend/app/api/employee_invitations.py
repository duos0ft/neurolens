import logging
from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    status,
)
from fastapi_csrf_protect import CsrfProtect
from fastapi_csrf_protect.exceptions import CsrfProtectError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.csrf import validate_request_origin
from app.core.database import async_session_factory, get_db
from app.core.permissions import require_admin
from app.models.email_outbox import EmailOutbox
from app.models.employee import Employee
from app.models.employee_invitation import EmployeeInvitation
from app.schemas.employee import (
    InvitationDeliveryStatus,
    InviteEmployeeRequest,
    InviteEmployeeResponse,
)
from app.schemas.invitation_provisioning import ProvisioningStatus
from app.services.auth0_management import Auth0ManagementService
from app.services.email_delivery import EmailDeliveryCoordinator
from app.services.email_outbox import EmailOutboxService
from app.services.employee_invitation import (
    EmployeeAlreadyExistsError,
    EmployeeInvitationService,
)
from app.services.invitation_provisioning import (
    InvitationProvisioningCoordinator,
)
from app.services.resend import ResendService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/employees/invitations",
    tags=["Employee Invitations"],
    dependencies=[
        Depends(require_admin),
        Depends(validate_request_origin),
    ],
)


@router.post(
    "",
    response_model=InviteEmployeeResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def invite_employee(
    request: Request,
    payload: InviteEmployeeRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    csrf_protect: Annotated[CsrfProtect, Depends()],
) -> InviteEmployeeResponse:
    try:
        await csrf_protect.validate_csrf(request)

    except CsrfProtectError as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing CSRF token",
        ) from error

    invitation_service = EmployeeInvitationService(db)

    try:
        employee = await invitation_service.create_invitation(
            email=str(payload.email),
            role=payload.role,
        )

    except EmployeeAlreadyExistsError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error

    employee_id = employee.user_id

    invitation_id = await db.scalar(
        select(EmployeeInvitation.id).where(
            EmployeeInvitation.employee_id == employee_id,
        )
    )

    if invitation_id is None:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Invitation record could not be retrieved",
        )

    await db.rollback()

    provisioning = InvitationProvisioningCoordinator(
        auth0=Auth0ManagementService(),
        invitations=invitation_service,
        session_factory=async_session_factory,
    )

    try:
        provisioning_result = await provisioning.provision_invitation(invitation_id)

        if provisioning_result.status == ProvisioningStatus.COMPLETED:
            outbox_id = await db.scalar(
                select(EmailOutbox.id).where(
                    EmailOutbox.invitation_id == invitation_id,
                )
            )

            await db.commit()

            if outbox_id is not None:
                delivery = EmailDeliveryCoordinator(
                    resend=ResendService(),
                    outbox=EmailOutboxService(db),
                    session_factory=async_session_factory,
                )

                await delivery.deliver_invitation(outbox_id)

    except Exception:
        logger.exception(
            "Invitation processing failed for invitation %s",
            invitation_id,
        )
        await db.rollback()

    result = await db.execute(
        select(
            Employee.user_id,
            Employee.email,
            Employee.role,
            Employee.status,
            EmployeeInvitation.status,
            EmailOutbox.status,
        )
        .join(
            EmployeeInvitation,
            EmployeeInvitation.employee_id == Employee.user_id,
        )
        .join(
            EmailOutbox,
            EmailOutbox.invitation_id == EmployeeInvitation.id,
        )
        .where(
            Employee.user_id == employee_id,
            EmployeeInvitation.id == invitation_id,
        )
    )

    row = result.one_or_none()
    await db.rollback()

    if row is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Invitation state could not be retrieved",
        )

    (
        user_id,
        email,
        role,
        employee_status,
        invitation_status,
        delivery_status,
    ) = row

    return InviteEmployeeResponse(
        id=user_id,
        email=email,
        role=role,
        status=employee_status,
        invitation_status=invitation_status,
        delivery_status=InvitationDeliveryStatus(delivery_status),
    )
