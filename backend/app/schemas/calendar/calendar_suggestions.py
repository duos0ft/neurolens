from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.ai.capabilities.calendar_extraction import CalendarEventType


class ReviewedCalendarEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    suggestion_index: int = Field(ge=0)

    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)

    event_type: CalendarEventType
    all_day: bool

    start_date: date | None = None
    end_date: date | None = None

    starts_at: datetime | None = None
    ends_at: datetime | None = None

    timezone: str = Field(min_length=1, max_length=100)

    @model_validator(mode="after")
    def validate_schedule(self):
        if self.all_day:
            if (
                self.start_date is None
                or self.end_date is None
                or self.starts_at is not None
                or self.ends_at is not None
            ):
                raise ValueError("All-day events require dates without times")

            if self.end_date <= self.start_date:
                raise ValueError("End date must be after start date")

        else:
            if (
                self.starts_at is None
                or self.ends_at is None
                or self.start_date is not None
                or self.end_date is not None
            ):
                raise ValueError("Timed events require start and end times")

            if self.starts_at.utcoffset() is None or self.ends_at.utcoffset() is None:
                raise ValueError("Timed events must be timezone-aware")

            if self.ends_at <= self.starts_at:
                raise ValueError("End time must be after start time")

        return self


class SaveReviewedCalendarEventsRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    events: list[ReviewedCalendarEvent] = Field(
        min_length=1,
        max_length=50,
    )

    @model_validator(mode="after")
    def validate_unique_suggestions(self):
        indices = [event.suggestion_index for event in self.events]

        if len(indices) != len(set(indices)):
            raise ValueError("Duplicate calendar suggestion indices")

        return self
