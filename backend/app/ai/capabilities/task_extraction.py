from datetime import date, time
from enum import StrEnum

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)


class TaskPriority(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ExtractedSubtask(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=200)

    @field_validator("title")
    @classmethod
    def normalize_title(cls, value: str) -> str:
        return " ".join(value.split())


class ExtractedTask(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(
        default=None,
        max_length=2000,
    )

    priority: TaskPriority | None = None

    due_date: date | None = None
    due_time: time | None = None

    source_text: str | None = None

    subtasks: list[ExtractedSubtask] = Field(
        default_factory=list,
    )

    @field_validator("title")
    @classmethod
    def normalize_title(cls, value: str) -> str:
        return " ".join(value.split())

    @field_validator("due_time")
    @classmethod
    def validate_due_time(cls, value: time | None) -> time | None:
        if value is None:
            return None

        if value.utcoffset() is not None:
            raise ValueError("Task deadline time must not contain a UTC offset")

        if value.second != 0 or value.microsecond != 0:
            raise ValueError("Task deadline time must have minute precision")

        return value

    @model_validator(mode="after")
    def validate_deadline(self):
        if self.due_time is not None and self.due_date is None:
            raise ValueError("A task deadline time requires a due date")

        return self


class TaskExtractionResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tasks: list[ExtractedTask] = Field(
        default_factory=list,
    )
