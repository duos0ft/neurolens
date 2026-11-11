import logging
import uuid
from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from app.ai.capabilities.task_extraction import ExtractedTask

logger = logging.getLogger(__name__)


class CreateConversationRequest(BaseModel):
    title: str | None = Field(
        default=None,
        max_length=150,
    )


class ConversationResponse(BaseModel):
    id: uuid.UUID
    title: str | None
    created_at: datetime
    updated_at: datetime


class ConversationTaskSuggestionsResponse(BaseModel):
    source_message_id: uuid.UUID | None = None
    tasks: list[ExtractedTask] = Field(default_factory=list)


class PolicyCitationResponse(BaseModel):
    number: int
    document_id: uuid.UUID
    document_slug: str
    document_title: str
    document_revision: int
    source_version: str
    effective_date: date | None
    section: str | None
    quotes: list[str] = Field(default_factory=list)


def citations_from_metadata(metadata: Any) -> list[PolicyCitationResponse]:
    if not metadata:
        return []

    # Imported lazily to keep schemas free of service-layer import cycles.
    from app.services.conversation_capability_metadata import (
        ConversationCapabilityMetadata,
    )

    try:
        parsed = ConversationCapabilityMetadata.from_dict(metadata)

    except (ValueError, TypeError, KeyError):
        logger.warning("Ignoring unreadable capability metadata on a stored message")
        return []

    return [
        PolicyCitationResponse(
            number=citation.number,
            document_id=citation.document_id,
            document_slug=citation.document_slug,
            document_title=citation.document_title,
            document_revision=citation.document_revision,
            source_version=citation.source_version,
            effective_date=citation.effective_date,
            section=citation.section,
            quotes=list(citation.quotes),
        )
        for citation in parsed.citations
    ]


class ConversationMessageResponse(BaseModel):
    id: uuid.UUID
    role: Literal["user", "assistant"]
    content: str
    model: str | None
    created_at: datetime
    task_suggestions: ConversationTaskSuggestionsResponse | None = None
    citations: list[PolicyCitationResponse] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def derive_citations(cls, value: Any) -> Any:
        if isinstance(value, dict) or not hasattr(value, "capability_metadata"):
            return value

        return {
            "id": value.id,
            "role": value.role,
            "content": value.content,
            "model": value.model,
            "created_at": value.created_at,
            "task_suggestions": value.task_suggestions,
            "citations": citations_from_metadata(value.capability_metadata),
        }


class ConversationDetailResponse(ConversationResponse):
    messages: list[ConversationMessageResponse]


class SendConversationMessageRequest(BaseModel):
    content: str = Field(
        min_length=1,
        max_length=10000,
    )


class UpdateConversationRequest(BaseModel):
    title: str = Field(
        min_length=1,
        max_length=100,
    )

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str) -> str:
        title = " ".join(value.split())

        if not title:
            raise ValueError("Conversation title cannot be empty")

        return title
