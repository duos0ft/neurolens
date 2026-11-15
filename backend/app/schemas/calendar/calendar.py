import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel


class CalendarEntryResponse(BaseModel):
    id: str
    source: Literal["task", "calendar_event"]
    title: str
    description: str | None

    event_type: Literal[
        "task_deadline",
        "meeting",
        "appointment",
        "event",
        "deadline",
    ]

    all_day: bool

    start_date: date | None
    end_date: date | None

    starts_at: datetime | None
    ends_at: datetime | None

    timezone: str

    task_id: uuid.UUID | None = None
    calendar_event_id: uuid.UUID | None = None

    status: str | None = None
    priority: str | None = None


class CalendarEntriesResponse(BaseModel):
    entries: list[CalendarEntryResponse]
