import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.pagination import PageResponse


class ContactPersonFields(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    email: str = Field(min_length=3, max_length=254)
    responsibility: str = Field(min_length=1, max_length=150)
    job_title: str | None = Field(default=None, max_length=150)
    department: str | None = Field(default=None, max_length=150)
    is_primary: bool = False

    @field_validator("name", "responsibility")
    @classmethod
    def normalize_required_text(cls, value: str) -> str:
        value = " ".join(value.split())

        if not value:
            raise ValueError("This field cannot be empty")

        return value

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        value = value.strip().lower()

        if (
            not value
            or value.count("@") != 1
            or not value.split("@")[0]
            or "." not in value.split("@")[1]
            or any(character.isspace() for character in value)
        ):
            raise ValueError("Enter a valid email address")

        return value

    @field_validator("job_title", "department")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None

        return " ".join(value.split()) or None


class CreateContactPersonRequest(ContactPersonFields):
    pass


class UpdateContactPersonRequest(ContactPersonFields):
    is_active: bool = True


class ContactPersonResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    email: str
    responsibility: str
    job_title: str | None
    department: str | None
    is_primary: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ContactPersonsPageResponse(PageResponse[ContactPersonResponse]):
    pass