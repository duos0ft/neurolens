import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class SaveTaskSuggestionsRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message_id: uuid.UUID
    selected_indices: list[int] = Field(min_length=1)


class SubtaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    task_id: uuid.UUID
    title: str
    completed: bool
    sort_order: int
    created_at: datetime
    updated_at: datetime


class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    employee_id: uuid.UUID
    title: str
    description: str | None
    status: str
    priority: str | None
    due_date: date | None
    source_message_id: uuid.UUID | None
    source_suggestion_index: int | None
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None
    subtasks: list[SubtaskResponse] = Field(default_factory=list)
