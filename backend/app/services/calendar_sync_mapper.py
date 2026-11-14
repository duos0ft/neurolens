from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.integrations.calendar.provider import (
    ExternalEventDraft,
    ExternalEventTime,
)
from app.models.calendar_event import CalendarEvent
from app.models.task import Task


class CalendarSyncMappingError(Exception):
    pass


class CalendarSyncMapper:
    @staticmethod
    def from_task(task: Task) -> ExternalEventDraft | None:
        if task.due_date is None or task.deleted_at is not None or task.archived_at is not None:
            return None

        title = task.title.strip()

        if not title:
            raise CalendarSyncMappingError("Task title cannot be empty")

        if task.status == "completed":
            title = f"✓ {title}"

        title = f"Deadline: {title}"

        description = task.description

        if task.due_time is None:
            if task.due_timezone is not None:
                raise CalendarSyncMappingError("Date-only task cannot have a timezone")

            return ExternalEventDraft(
                title=title,
                description=description,
                start=ExternalEventTime(
                    date=task.due_date,
                ),
                end=ExternalEventTime(
                    date=task.due_date + timedelta(days=1),
                ),
            )

        if not task.due_timezone:
            raise CalendarSyncMappingError("Timed task deadline requires a timezone")

        try:
            zone = ZoneInfo(task.due_timezone)
        except (ZoneInfoNotFoundError, ValueError) as error:
            raise CalendarSyncMappingError("Invalid task deadline timezone") from error

        start = datetime.combine(
            task.due_date,
            task.due_time,
            tzinfo=zone,
        )

        start_utc = start.astimezone(timezone.utc)
        end = (start_utc + timedelta(minutes=1)).astimezone(zone)

        return ExternalEventDraft(
            title=title,
            description=description,
            start=ExternalEventTime(
                datetime=start,
                timezone=task.due_timezone,
            ),
            end=ExternalEventTime(
                datetime=end,
                timezone=task.due_timezone,
            ),
        )

    @staticmethod
    def from_calendar_event(
        event: CalendarEvent,
    ) -> ExternalEventDraft:
        title = event.title.strip()

        if not title:
            raise CalendarSyncMappingError("Calendar event title cannot be empty")

        if event.all_day:
            if (
                event.start_date is None
                or event.end_date is None
                or event.end_date <= event.start_date
            ):
                raise CalendarSyncMappingError("Invalid all-day calendar event")

            return ExternalEventDraft(
                title=title,
                description=event.description,
                start=ExternalEventTime(
                    date=event.start_date,
                ),
                end=ExternalEventTime(
                    date=event.end_date,
                ),
            )

        if event.starts_at is None or event.ends_at is None:
            raise CalendarSyncMappingError("Timed calendar event requires start and end")

        if (
            event.starts_at.tzinfo is None
            or event.ends_at.tzinfo is None
            or event.starts_at.utcoffset() is None
            or event.ends_at.utcoffset() is None
        ):
            raise CalendarSyncMappingError("Calendar event datetimes must be timezone-aware")

        if event.ends_at <= event.starts_at:
            raise CalendarSyncMappingError("Calendar event end must follow start")

        try:
            zone = ZoneInfo(event.timezone)
        except (ZoneInfoNotFoundError, ValueError) as error:
            raise CalendarSyncMappingError("Invalid calendar event timezone") from error

        start = event.starts_at.astimezone(zone)
        end = event.ends_at.astimezone(zone)

        return ExternalEventDraft(
            title=title,
            description=event.description,
            start=ExternalEventTime(
                datetime=start,
                timezone=event.timezone,
            ),
            end=ExternalEventTime(
                datetime=end,
                timezone=event.timezone,
            ),
        )
