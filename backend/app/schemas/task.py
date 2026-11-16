import uuid
from datetime import date, datetime, time
from typing import Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

TaskPriority = Literal["low", "medium", "high"]
TaskStatus = Literal["todo", "in_progress", "completed"]


class TaskDeadlineFields(BaseModel):
    """
    Shared deadline validation for task creation, editing,
    and reviewed task suggestions.
    """

    due_date: date | None = None
    due_time: time | None = None
    due_timezone: str | None = None

    @field_validator("due_time")
    @classmethod
    def validate_due_time(
        cls,
        value: time | None,
    ) -> time | None:
        if value is None:
            return None

        if value.utcoffset() is not None:
            raise ValueError("Deadline time must not contain a UTC offset")

        if value.second != 0 or value.microsecond != 0:
            raise ValueError("Deadline time must have minute precision")

        return value

    @field_validator("due_timezone")
    @classmethod
    def validate_due_timezone(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        timezone = value.strip()

        try:
            ZoneInfo(timezone)
        except (ZoneInfoNotFoundError, ValueError) as error:
            raise ValueError("Invalid IANA timezone") from error

        return timezone

    @model_validator(mode="after")
    def validate_deadline(self):
        if self.due_time is not None and self.due_date is None:
            raise ValueError("A deadline time requires a due date")

        if self.due_timezone is not None and (self.due_date is None or self.due_time is None):
            raise ValueError("A deadline timezone requires a date and time")

        return self


class ReviewedSubtask(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(
        min_length=1,
        max_length=200,
    )

    @field_validator("title")
    @classmethod
    def normalize_title(cls, value: str) -> str:
        value = " ".join(value.split())

        if not value:
            raise ValueError("Subtask title cannot be empty")

        return value


class ReviewedTask(TaskDeadlineFields):
    model_config = ConfigDict(extra="forbid")

    suggestion_index: int = Field(ge=0)

    title: str = Field(
        min_length=1,
        max_length=200,
    )

    description: str | None = Field(
        default=None,
        max_length=5000,
    )

    priority: TaskPriority | None = None

    subtasks: list[ReviewedSubtask] = Field(
        default_factory=list,
        max_length=50,
    )

    @field_validator("title")
    @classmethod
    def normalize_title(cls, value: str) -> str:
        value = " ".join(value.split())

        if not value:
            raise ValueError("Task title cannot be empty")

        return value

    @field_validator("description")
    @classmethod
    def normalize_description(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        value = value.strip()

        return value or None


class SaveReviewedTasksRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message_id: uuid.UUID

    tasks: list[ReviewedTask] = Field(
        min_length=1,
        max_length=50,
    )

    @model_validator(mode="after")
    def validate_unique_suggestions(
        self,
    ) -> "SaveReviewedTasksRequest":
        indices = [task.suggestion_index for task in self.tasks]

        if len(indices) != len(set(indices)):
            raise ValueError("Duplicate task suggestion indices are not allowed")

        return self


class SaveTaskSuggestionsRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message_id: uuid.UUID

    selected_indices: list[int] = Field(
        min_length=1,
    )


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
    due_time: time | None
    due_timezone: str | None

    source_message_id: uuid.UUID | None
    source_suggestion_index: int | None

    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None
    archived_at: datetime | None
    deleted_at: datetime | None

    subtasks: list[SubtaskResponse] = Field(
        default_factory=list,
    )


class TaskStatsResponse(BaseModel):
    todo: int
    in_progress: int
    completed: int


class UpdateTaskStatusRequest(BaseModel):
    status: TaskStatus


class CreateSubtaskRequest(BaseModel):
    title: str = Field(
        min_length=1,
        max_length=200,
    )


class UpdateSubtaskRequest(BaseModel):
    id: uuid.UUID | None = None

    title: str = Field(
        min_length=1,
        max_length=200,
    )


class CreateTaskRequest(TaskDeadlineFields):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(
        min_length=1,
        max_length=255,
    )

    description: str | None = None
    priority: TaskPriority | None = None

    subtasks: list[CreateSubtaskRequest] = Field(
        default_factory=list,
        max_length=50,
    )


class UpdateTaskRequest(TaskDeadlineFields):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(
        min_length=1,
        max_length=255,
    )

    description: str | None = None
    priority: TaskPriority | None = None

    subtasks: list[UpdateSubtaskRequest] | None = Field(
        default=None,
        max_length=50,
    )


class UpdateSubtaskCompletionRequest(BaseModel):
    completed: bool
