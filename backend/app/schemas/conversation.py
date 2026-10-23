import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


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


class ConversationMessageResponse(BaseModel):
    id: uuid.UUID
    role: Literal["user", "assistant"]
    content: str
    model: str | None
    created_at: datetime


class ConversationDetailResponse(ConversationResponse):
    messages: list[ConversationMessageResponse]


class SendConversationMessageRequest(BaseModel):
    content: str = Field(
        min_length=1,
        max_length=10000,
    )
