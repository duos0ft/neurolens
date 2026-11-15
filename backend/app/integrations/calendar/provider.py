from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import StrEnum


class ExternalEventStatus(StrEnum):
    CONFIRMED = "confirmed"
    TENTATIVE = "tentative"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class ExternalCalendar:
    id: str
    name: str
    primary: bool
    timezone: str | None = None
    can_write: bool = False


@dataclass(frozen=True)
class ExternalEventTime:
    date: date | None = None
    datetime: datetime | None = None
    timezone: str | None = None

    def __post_init__(self) -> None:
        if (self.date is None) == (self.datetime is None):
            raise ValueError("Exactly one of date or datetime must be provided")

        if self.datetime is not None:
            if self.datetime.tzinfo is None or self.datetime.utcoffset() is None:
                raise ValueError("Timed event values must be timezone-aware")


@dataclass(frozen=True)
class ExternalCalendarEvent:
    id: str
    calendar_id: str
    title: str
    start: ExternalEventTime
    end: ExternalEventTime
    status: ExternalEventStatus = ExternalEventStatus.CONFIRMED
    description: str | None = None
    location: str | None = None
    recurring_event_id: str | None = None
    original_start: ExternalEventTime | None = None
    provider_etag: str | None = None
    provider_ical_uid: str | None = None
    provider_metadata: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        is_all_day_start = self.start.date is not None
        is_all_day_end = self.end.date is not None

        if is_all_day_start != is_all_day_end:
            raise ValueError("Event start and end must both be dates or datetimes")

        if is_all_day_start:
            if self.end.date <= self.start.date:
                raise ValueError("All-day event end date must follow start date")
        else:
            if self.end.datetime <= self.start.datetime:
                raise ValueError("Timed event end must follow start")

        if self.original_start is not None:
            if (self.original_start.date is not None) != is_all_day_start:
                raise ValueError("Recurring instance start type must match event type")

    @property
    def is_all_day(self) -> bool:
        return self.start.date is not None

    @property
    def is_recurring_instance(self) -> bool:
        return self.recurring_event_id is not None


@dataclass(frozen=True)
class ExternalEventDraft:
    title: str
    start: ExternalEventTime
    end: ExternalEventTime
    description: str | None = None
    location: str | None = None

    def __post_init__(self) -> None:
        if (self.start.date is None) != (self.end.date is None):
            raise ValueError("Draft start and end must use the same time representation")

        if self.start.date is not None:
            if self.end.date <= self.start.date:
                raise ValueError("All-day event end date must follow start date")
        elif self.end.datetime <= self.start.datetime:
            raise ValueError("Timed event end must follow start")


@dataclass(frozen=True)
class ExternalEventPage:
    events: list[ExternalCalendarEvent]
    next_page_token: str | None = None


class CalendarProviderClient(ABC):
    @abstractmethod
    async def list_calendars(self) -> list[ExternalCalendar]:
        raise NotImplementedError

    @abstractmethod
    async def list_events(
        self,
        calendar_id: str,
        start_at: datetime,
        end_at: datetime,
        page_token: str | None = None,
    ) -> ExternalEventPage:
        raise NotImplementedError

    @abstractmethod
    async def create_event(
        self,
        calendar_id: str,
        event: ExternalEventDraft,
        idempotency_key: str,
    ) -> ExternalCalendarEvent:
        raise NotImplementedError
