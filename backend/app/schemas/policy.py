import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

PolicyCategory = Literal[
    "leave",
    "remote_work",
    "working_hours",
    "communication",
    "accessibility",
    "information_security",
    "other",
]

PolicyDirectoryStatus = Literal[
    "no_document",
    "pending",
    "processing",
    "ready",
    "failed",
    "published",
    "archived",
]


class CreatePolicyDocumentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    category: PolicyCategory = "other"

    @field_validator("title")
    @classmethod
    def normalize_title(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Policy title cannot be empty")

        return value

    @field_validator("description")
    @classmethod
    def normalize_description(cls, value: str | None) -> str | None:
        if value is None:
            return None

        return value.strip() or None


class PolicyDocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    description: str | None
    category: PolicyCategory
    created_by: uuid.UUID | None
    created_at: datetime
    updated_at: datetime


from datetime import date
from typing import Literal

PolicyIngestionStatus = Literal[
    "pending",
    "processing",
    "ready",
    "failed",
]

PolicyPublicationStatus = Literal[
    "draft",
    "published",
    "archived",
]


class PolicyVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    document_id: uuid.UUID
    version_number: int
    original_filename: str
    content_type: str
    file_size_bytes: int
    effective_date: date | None
    ingestion_status: PolicyIngestionStatus
    publication_status: PolicyPublicationStatus
    ingestion_error_code: str | None
    uploaded_by: uuid.UUID | None
    created_at: datetime
    updated_at: datetime
    published_at: datetime | None
    archived_at: datetime | None


class PolicyDocumentListResponse(BaseModel):
    documents: list[PolicyDocumentResponse]


class PolicyVersionListResponse(BaseModel):
    versions: list[PolicyVersionResponse]


class PublishedPolicyResponse(BaseModel):
    id: uuid.UUID
    title: str
    description: str | None
    category: PolicyCategory
    version_id: uuid.UUID
    version_number: int
    effective_date: date | None
    published_at: datetime


class PublishedPolicyListResponse(BaseModel):
    documents: list[PublishedPolicyResponse]


class AdminPolicyDocumentResponse(PolicyDocumentResponse):
    latest_version_number: int | None = None
    status: PolicyDirectoryStatus = "no_document"


class AdminPolicyDocumentListResponse(BaseModel):
    documents: list[AdminPolicyDocumentResponse]
