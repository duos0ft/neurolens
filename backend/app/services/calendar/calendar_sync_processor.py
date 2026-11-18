import logging
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.integrations.calendar.google_events import (
    GoogleCalendarAuthorizationError,
    GoogleCalendarEventError,
    GoogleCalendarEventNotFoundError,
    GoogleCalendarEventService,
    GoogleCalendarRetryableError,
)
from app.integrations.calendar.provider import ExternalEventDraft
from app.models.calendar_event import CalendarEvent
from app.models.calendar_integration import CalendarIntegration
from app.models.calendar_sync_record import CalendarSyncRecord
from app.models.task import Task
from app.services.calendar.calendar_sync_completion import (
    CalendarSyncCompletionService,
)
from app.services.calendar.calendar_sync_mapper import (
    CalendarSyncMapper,
    CalendarSyncMappingError,
)
from app.services.calendar.calendar_sync_worker import (
    CalendarSyncWorker,
    ClaimedCalendarSyncJob,
)
from app.services.calendar.google_calendar_tokens import (
    GoogleCalendarReconnectRequiredError,
    GoogleCalendarTokenError,
    GoogleCalendarTokenService,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CalendarSyncContext:
    access_token: str
    draft: ExternalEventDraft | None


@dataclass(frozen=True)
class CalendarSyncOutcome:
    external_calendar_id: str | None = None
    external_event_id: str | None = None
    deleted: bool = False


class CalendarSyncProcessor:
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        self.session_factory = session_factory

    async def process_next(self) -> bool:
        async with self.session_factory() as db:
            jobs = await CalendarSyncWorker(db).claim_jobs(limit=1)

        if not jobs:
            return False

        await self._process_job(jobs[0])
        return True

    async def _load_context(
        self,
        job: ClaimedCalendarSyncJob,
    ) -> CalendarSyncContext | None:
        async with self.session_factory() as db:
            record = await db.scalar(
                select(CalendarSyncRecord).where(
                    CalendarSyncRecord.id == job.id,
                    CalendarSyncRecord.integration_id == job.integration_id,
                    CalendarSyncRecord.status == "syncing",
                    CalendarSyncRecord.attempt_id == job.attempt_id,
                    CalendarSyncRecord.revision == job.revision,
                    CalendarSyncRecord.lease_expires_at > datetime.now(timezone.utc),
                )
            )

            if record is None:
                return None

            integration = await db.scalar(
                select(CalendarIntegration).where(
                    CalendarIntegration.id == job.integration_id,
                    CalendarIntegration.provider == "google",
                )
            )

            if integration is None:
                return None

            draft = None

            if job.operation == "upsert":
                if job.source_type == "task":
                    task = await db.scalar(
                        select(Task).where(
                            Task.id == job.source_id,
                            Task.employee_id == integration.employee_id,
                        )
                    )

                    if task is not None:
                        draft = CalendarSyncMapper.from_task(task)

                elif job.source_type == "calendar_event":
                    event = await db.scalar(
                        select(CalendarEvent).where(
                            CalendarEvent.id == job.source_id,
                            CalendarEvent.employee_id == integration.employee_id,
                        )
                    )

                    if event is not None:
                        draft = CalendarSyncMapper.from_calendar_event(event)

                else:
                    raise CalendarSyncMappingError("Unsupported calendar sync source")

            token = await GoogleCalendarTokenService(db).get_access_token(integration.employee_id)

            return CalendarSyncContext(
                access_token=token.token,
                draft=draft,
            )

    async def _execute_google_operation(
        self,
        job: ClaimedCalendarSyncJob,
        context: CalendarSyncContext,
    ) -> CalendarSyncOutcome:
        service = GoogleCalendarEventService(context.access_token)

        calendar_id = job.external_calendar_id or "primary"
        idempotency_key = str(job.id)

        event_id = job.external_event_id or service._event_id(idempotency_key)

        if job.operation == "delete" or context.draft is None:
            await service.delete_event(
                calendar_id=calendar_id,
                event_id=event_id,
                idempotency_key=idempotency_key,
            )

            return CalendarSyncOutcome(deleted=True)

        if job.external_event_id:
            try:
                event = await service.update_event(
                    calendar_id=calendar_id,
                    event_id=event_id,
                    event=context.draft,
                    idempotency_key=idempotency_key,
                )

                return CalendarSyncOutcome(
                    external_calendar_id=calendar_id,
                    external_event_id=event.id,
                )

            except GoogleCalendarEventNotFoundError:
                pass

        created = await service.create_event(
            calendar_id=calendar_id,
            event=context.draft,
            idempotency_key=idempotency_key,
        )

        event = await service.update_event(
            calendar_id=calendar_id,
            event_id=created.id,
            event=context.draft,
            idempotency_key=idempotency_key,
        )

        return CalendarSyncOutcome(
            external_calendar_id=calendar_id,
            external_event_id=event.id,
        )

    async def _complete_success(
        self,
        job: ClaimedCalendarSyncJob,
        outcome: CalendarSyncOutcome,
    ) -> None:
        async with self.session_factory() as db:
            await CalendarSyncCompletionService(db).complete_success(
                job=job,
                external_calendar_id=outcome.external_calendar_id,
                external_event_id=outcome.external_event_id,
                deleted=outcome.deleted,
            )

    async def _complete_failure(
        self,
        job: ClaimedCalendarSyncJob,
        error_code: str,
        retryable: bool,
    ) -> None:
        async with self.session_factory() as db:
            await CalendarSyncCompletionService(db).complete_failure(
                job=job,
                error_code=error_code,
                retryable=retryable,
            )

    async def _process_job(
        self,
        job: ClaimedCalendarSyncJob,
    ) -> None:
        try:
            context = await self._load_context(job)

            if context is None:
                await self._complete_failure(
                    job,
                    error_code="superseded",
                    retryable=True,
                )
                return

            outcome = await self._execute_google_operation(
                job,
                context,
            )

        except GoogleCalendarReconnectRequiredError:
            await self._complete_failure(
                job,
                error_code="google_reconnect_required",
                retryable=False,
            )
            return

        except GoogleCalendarAuthorizationError:
            await self._complete_failure(
                job,
                error_code="google_authorization_failed",
                retryable=False,
            )
            return

        except (
            GoogleCalendarRetryableError,
            GoogleCalendarTokenError,
        ):
            await self._complete_failure(
                job,
                error_code="google_temporarily_unavailable",
                retryable=True,
            )
            return

        except CalendarSyncMappingError:
            await self._complete_failure(
                job,
                error_code="invalid_source_data",
                retryable=False,
            )
            return

        except GoogleCalendarEventError:
            await self._complete_failure(
                job,
                error_code="google_event_rejected",
                retryable=False,
            )
            return

        except Exception:
            logger.exception("Unexpected calendar synchronization failure")

            await self._complete_failure(
                job,
                error_code="unexpected_error",
                retryable=True,
            )
            return

        await self._complete_success(
            job,
            outcome,
        )
