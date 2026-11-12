import uuid
from datetime import datetime
from typing import Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, Field, field_validator

from app.ai.capabilities.calendar_extraction import ExtractedCalendarEvent
from app.ai.capabilities.task_extraction import ExtractedTask


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


class ConversationCalendarSuggestionsResponse(BaseModel):
    source_message_id: uuid.UUID | None = None
    events: list[ExtractedCalendarEvent] = Field(default_factory=list)


class ConversationMessageResponse(BaseModel):
    id: uuid.UUID
    role: Literal["user", "assistant"]
    content: str
    model: str | None
    created_at: datetime
    task_suggestions: ConversationTaskSuggestionsResponse | None = None
    calendar_suggestions: ConversationCalendarSuggestionsResponse | None = None


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
