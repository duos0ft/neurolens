import uuid
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, EmailStr


class EmployeeRole(StrEnum):
    ADMIN = "admin"
    EMPLOYEE = "employee"


class EmployeeStatus(StrEnum):
    INVITED = "invited"
    ACTIVE = "active"
    SUSPENDED = "suspended"


class EmployeeResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )

    id: uuid.UUID = Field(validation_alias="user_id")
    role: EmployeeRole
    status: EmployeeStatus
    created_at: datetime


class EmployeeListResponse(BaseModel):
    employees: list[EmployeeResponse]


class InviteEmployeeRequest(BaseModel):
    email: EmailStr
    role: EmployeeRole = EmployeeRole.EMPLOYEE


class InviteEmployeeResponse(BaseModel):
    id: uuid.UUID
    email: EmailStr
    role: EmployeeRole
    status: EmployeeStatus