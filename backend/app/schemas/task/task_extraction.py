import uuid

from pydantic import BaseModel, ConfigDict, Field

from app.ai.capabilities.task_extraction import TaskExtractionResult


class ConversationTaskExtractionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request: str = Field(min_length=1, max_length=1000)


class TaskExtractionResponse(TaskExtractionResult):
    pass


class ResolvedTaskExtractionResponse(TaskExtractionResult):
    source_message_id: uuid.UUID
