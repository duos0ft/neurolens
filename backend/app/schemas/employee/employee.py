import uuid
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.schemas.pagination.pagination import PageResponse


class EmployeeStatus(StrEnum):
    INVITED = "invited"
    ACTIVE = "active"
    SUSPENDED = "suspended"


class EmployeeRole(StrEnum):
    ADMIN = "admin"
    EMPLOYEE = "employee"


class InvitationStatus(StrEnum):
    PENDING = "pending"
    PROVISIONING = "provisioning"
    RECONCILIATION_REQUIRED = "reconciliation_required"
    READY = "ready"
    ACCEPTED = "accepted"
    FAILED = "failed"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class InvitationDeliveryStatus(StrEnum):
    PENDING = "pending"
    SENDING = "sending"
    SENT = "sent"
    FAILED = "failed"
    RECONCILIATION_REQUIRED = "reconciliation_required"


class AuthenticatedEmployeeResponse(BaseModel):
    id: uuid.UUID
    email: EmailStr | None
    role: EmployeeRole
    status: EmployeeStatus
    display_name: str | None = None
    job_title: str | None = None
    department: str | None = None
    team: str | None = None


class EmployeeResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )

    id: uuid.UUID = Field(validation_alias="user_id")
    email: EmailStr | None
    display_name: str | None = None
    role: EmployeeRole
    status: EmployeeStatus
    invitation_status: InvitationStatus | None = None
    created_at: datetime


class EmployeeListResponse(PageResponse[EmployeeResponse]):
    pass


class InviteEmployeeRequest(BaseModel):
    email: EmailStr
    role: EmployeeRole = EmployeeRole.EMPLOYEE


class InviteEmployeeResponse(BaseModel):
    id: uuid.UUID
    email: EmailStr
    role: EmployeeRole
    status: EmployeeStatus
    invitation_status: InvitationStatus
    delivery_status: InvitationDeliveryStatus


class UpdateEmployeeProfileRequest(BaseModel):
    display_name: str | None = Field(default=None, max_length=100)
    job_title: str | None = Field(default=None, max_length=150)
    department: str | None = Field(default=None, max_length=150)
    team: str | None = Field(default=None, max_length=150)
    timezone: str | None = Field(default=None, max_length=100)


class InvitationValidationResponse(BaseModel):
    email: EmailStr
    role: EmployeeRole
    expires_at: datetime
