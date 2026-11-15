import uuid
from datetime import datetime
from typing import Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, Field, field_validator, model_validator

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

    @model_validator(mode="before")
    @classmethod
    def normalize_legacy_events(cls, value):
        if not isinstance(value, dict):
            return value

        events = value.get("events")

        if not isinstance(events, list):
            return value

        normalized_events = []

        for event in events:
            if not isinstance(event, dict):
                normalized_events.append(event)
                continue

            normalized_event = dict(event)
            inferred = normalized_event.pop("end_time_inferred", None)

            if "end_time_source" not in normalized_event:
                if normalized_event.get("all_day") is True:
                    normalized_event["end_time_source"] = None
                elif inferred is True:
                    normalized_event["end_time_source"] = "default"
                elif inferred is False:
                    normalized_event["end_time_source"] = "explicit"

            normalized_events.append(normalized_event)

        return {
            **value,
            "events": normalized_events,
        }


class ConversationClarificationsResponse(BaseModel):
    version: Literal[1] = 1
    questions: list[str] = Field(default_factory=list)


class ConversationMessageResponse(BaseModel):
    id: uuid.UUID
    role: Literal["user", "assistant"]
    content: str
    model: str | None
    created_at: datetime
    task_suggestions: ConversationTaskSuggestionsResponse | None = None
    calendar_suggestions: ConversationCalendarSuggestionsResponse | None = None
    clarifications: ConversationClarificationsResponse | None = None


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
