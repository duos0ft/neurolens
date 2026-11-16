import uuid
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.calendar_event import CalendarEvent
from app.models.task import Task
from app.schemas.calendar.calendar import CalendarEntryResponse

TASK_DEADLINE_DURATION = timedelta(minutes=1)


class CalendarService:
    def __init__(
        self,
        db: AsyncSession,
    ) -> None:
        self.db = db

    async def get_entries(
        self,
        employee_id: uuid.UUID,
        start: date,
        end: date,
        calendar_timezone: str,
    ) -> list[CalendarEntryResponse]:
        if end <= start:
            raise ValueError("End date must be after start date")

        tz = ZoneInfo(calendar_timezone)

        range_start = datetime.combine(
            start,
            time.min,
            tzinfo=tz,
        ).astimezone(timezone.utc)

        range_end = datetime.combine(
            end,
            time.min,
            tzinfo=tz,
        ).astimezone(timezone.utc)

        events = await self._get_events(
            employee_id=employee_id,
            start=start,
            end=end,
            range_start=range_start,
            range_end=range_end,
        )

        tasks = await self._get_task_deadlines(
            employee_id=employee_id,
            start=start,
            end=end,
        )

        entries = [self._map_event(event) for event in events]

        for task in tasks:
            entry = self._map_task(
                task=task,
                calendar_timezone=calendar_timezone,
            )

            if entry.all_day:
                if (
                    entry.start_date is not None
                    and entry.end_date is not None
                    and entry.start_date < end
                    and entry.end_date > start
                ):
                    entries.append(entry)

                continue

            if (
                entry.starts_at is not None
                and entry.ends_at is not None
                and entry.starts_at < range_end
                and entry.ends_at > range_start
            ):
                entries.append(entry)

        entries.sort(
            key=lambda entry: (
                entry.start_date if entry.all_day else entry.starts_at.astimezone(tz).date(),
                0 if entry.all_day else 1,
                "" if entry.all_day else entry.starts_at.astimezone(tz).isoformat(),
                entry.id,
            )
        )

        return entries

    async def _get_events(
        self,
        employee_id: uuid.UUID,
        start: date,
        end: date,
        range_start: datetime,
        range_end: datetime,
    ) -> list[CalendarEvent]:
        result = await self.db.scalars(
            select(CalendarEvent).where(
                CalendarEvent.employee_id == employee_id,
                or_(
                    and_(
                        CalendarEvent.all_day.is_(True),
                        CalendarEvent.start_date < end,
                        CalendarEvent.end_date > start,
                    ),
                    and_(
                        CalendarEvent.all_day.is_(False),
                        CalendarEvent.starts_at < range_end,
                        CalendarEvent.ends_at > range_start,
                    ),
                ),
            )
        )

        return list(result.all())

    async def _get_task_deadlines(
        self,
        employee_id: uuid.UUID,
        start: date,
        end: date,
    ) -> list[Task]:
        candidate_start = start - timedelta(days=2)
        candidate_end = end + timedelta(days=2)

        result = await self.db.scalars(
            select(Task)
            .where(
                Task.employee_id == employee_id,
                Task.due_date.is_not(None),
                Task.archived_at.is_(None),
                Task.deleted_at.is_(None),
                or_(
                    and_(
                        Task.due_time.is_(None),
                        Task.due_date >= start,
                        Task.due_date < end,
                    ),
                    and_(
                        Task.due_time.is_not(None),
                        Task.due_date >= candidate_start,
                        Task.due_date < candidate_end,
                    ),
                ),
            )
            .order_by(
                Task.due_date,
                Task.due_time,
                Task.id,
            )
        )

        return list(result.all())

    def _map_event(
        self,
        event: CalendarEvent,
    ) -> CalendarEntryResponse:
        return CalendarEntryResponse(
            id=f"event:{event.id}",
            source="calendar_event",
            title=event.title,
            description=event.description,
            event_type=event.event_type,
            all_day=event.all_day,
            start_date=event.start_date,
            end_date=event.end_date,
            starts_at=event.starts_at,
            ends_at=event.ends_at,
            timezone=event.timezone,
            calendar_event_id=event.id,
        )

    def _map_task(
        self,
        task: Task,
        calendar_timezone: str,
    ) -> CalendarEntryResponse:
        if task.due_date is None:
            raise ValueError("Task deadline date is required")

        if task.due_time is None:
            return CalendarEntryResponse(
                id=f"task:{task.id}",
                source="task",
                title=task.title,
                description=task.description,
                event_type="task_deadline",
                all_day=True,
                start_date=task.due_date,
                end_date=task.due_date + timedelta(days=1),
                starts_at=None,
                ends_at=None,
                timezone=calendar_timezone,
                task_id=task.id,
                status=task.status,
                priority=task.priority,
            )

        if task.due_timezone is None:
            raise ValueError("Timed task deadline requires a timezone")

        task_timezone = ZoneInfo(task.due_timezone)

        local_deadline = datetime.combine(
            task.due_date,
            task.due_time,
            tzinfo=task_timezone,
        )

        starts_at = local_deadline.astimezone(timezone.utc)
        ends_at = starts_at + TASK_DEADLINE_DURATION

        return CalendarEntryResponse(
            id=f"task:{task.id}",
            source="task",
            title=task.title,
            description=task.description,
            event_type="task_deadline",
            all_day=False,
            start_date=None,
            end_date=None,
            starts_at=starts_at,
            ends_at=ends_at,
            timezone=task.due_timezone,
            task_id=task.id,
            status=task.status,
            priority=task.priority,
        )
