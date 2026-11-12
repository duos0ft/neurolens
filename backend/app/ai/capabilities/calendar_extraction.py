from datetime import date, datetime, timezone
from enum import StrEnum
from zoneinfo import ZoneInfoNotFoundError, ZoneInfo

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)


class CalendarEventType(StrEnum):
    MEETING = "meeting"
    APPOINTMENT = "appointment"
    EVENT = "event"
    DEADLINE = "deadline"


class CalendarEndTimeSource(StrEnum):
    EXPLICIT = "explicit"
    DURATION = "duration"
    DEFAULT = "default"


class ExtractedCalendarEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)

    event_type: CalendarEventType

    all_day: bool

    start_date: date | None = None
    end_date: date | None = None

    starts_at: datetime | None = None
    ends_at: datetime | None = None

    end_time_source: CalendarEndTimeSource | None = None

    timezone: str

    source_text: str | None = None

    @field_validator("title")
    @classmethod
    def normalize_title(cls, value: str) -> str:
        return " ".join(value.split())

    @model_validator(mode="after")
    def validate_date_range(self):
        try:
            zone = ZoneInfo(self.timezone)
        except (ZoneInfoNotFoundError, ValueError) as error:
            raise ValueError("Invalid IANA timezone") from error

        if self.all_day:
            if (
                self.start_date is None
                or self.end_date is None
                or self.starts_at is not None
                or self.ends_at is not None
            ):
                raise ValueError("All-day events require start_date and end_date")

            if self.end_date <= self.start_date:
                raise ValueError("End date must be after start date")

            if self.end_time_source is not None:
                raise ValueError("All-day events cannot have an end time source")

            return self

        if (
            self.starts_at is None
            or self.ends_at is None
            or self.start_date is not None
            or self.end_date is not None
        ):
            raise ValueError("Timed events require starts_at and ends_at")

        if self.starts_at.utcoffset() is None or self.ends_at.utcoffset() is None:
            raise ValueError("Timed events require timezone-aware datetimes")

        if self.ends_at <= self.starts_at:
            raise ValueError("End time must be after start time")

        if self.end_time_source is None:
            raise ValueError("Timed events require an end time source")

        for timestamp in (self.starts_at, self.ends_at):
            actual_offset = timestamp.utcoffset()

            local_timestamp = timestamp.astimezone(
                timezone.utc,
            ).astimezone(zone)

            expected_offset = local_timestamp.utcoffset()

            if actual_offset != expected_offset:
                raise ValueError("Timestamp UTC offset does not match the IANA timezone")

            if timestamp.replace(tzinfo=None) != local_timestamp.replace(
                tzinfo=None,
            ):
                raise ValueError("Timestamp local time does not match the IANA timezone")

        return self


class CalendarExtractionResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    events: list[ExtractedCalendarEvent] = Field(
        default_factory=list,
    )
