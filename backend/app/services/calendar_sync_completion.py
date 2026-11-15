import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.calendar_sync_record import CalendarSyncRecord
from app.services.calendar_sync_worker import ClaimedCalendarSyncJob


MAX_RETRY_ATTEMPTS = 8
INITIAL_RETRY_DELAY_SECONDS = 15
MAX_RETRY_DELAY_SECONDS = 3600


class CalendarSyncCompletionService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def _get_claimed_record(
        self,
        job: ClaimedCalendarSyncJob,
    ) -> CalendarSyncRecord | None:
        return await self.db.scalar(
            select(CalendarSyncRecord)
            .where(
                CalendarSyncRecord.id == job.id,
                CalendarSyncRecord.integration_id == job.integration_id,
                CalendarSyncRecord.status == "syncing",
                CalendarSyncRecord.attempt_id == job.attempt_id,
            )
            .with_for_update()
        )

    @staticmethod
    def _release_claim(
        record: CalendarSyncRecord,
    ) -> None:
        record.attempt_id = None
        record.lease_expires_at = None

    @classmethod
    def _mark_pending(
        cls,
        record: CalendarSyncRecord,
    ) -> None:
        record.status = "pending"
        record.retry_count = 0
        record.next_retry_at = None
        record.last_error_code = None
        cls._release_claim(record)

    async def complete_success(
        self,
        job: ClaimedCalendarSyncJob,
        external_calendar_id: str | None = None,
        external_event_id: str | None = None,
        deleted: bool = False,
    ) -> bool:
        is_deletion = job.operation == "delete" or deleted

        if not is_deletion:
            if not external_calendar_id or not external_event_id:
                raise ValueError("Successful upsert requires external event identifiers")

        try:
            record = await self._get_claimed_record(job)

            if record is None:
                await self.db.rollback()
                return False

            if is_deletion:
                record.external_calendar_id = None
                record.external_event_id = None
            else:
                record.external_calendar_id = external_calendar_id
                record.external_event_id = external_event_id

            record.last_synced_at = datetime.now(timezone.utc)

            if record.revision != job.revision:
                self._mark_pending(record)
            else:
                record.status = "synced"
                record.retry_count = 0
                record.next_retry_at = None
                record.last_error_code = None
                self._release_claim(record)

            await self.db.commit()
            return True

        except Exception:
            await self.db.rollback()
            raise

    async def complete_failure(
        self,
        job: ClaimedCalendarSyncJob,
        error_code: str,
        retryable: bool,
    ) -> bool:
        if not error_code or len(error_code) > 100:
            raise ValueError("Invalid calendar synchronization error code")

        try:
            record = await self._get_claimed_record(job)

            if record is None:
                await self.db.rollback()
                return False

            if record.revision != job.revision:
                self._mark_pending(record)
                await self.db.commit()
                return True

            retry_count = record.retry_count + 1

            record.retry_count = retry_count
            record.last_error_code = error_code

            self._release_claim(record)

            if retryable and retry_count < MAX_RETRY_ATTEMPTS:
                delay_seconds = min(
                    INITIAL_RETRY_DELAY_SECONDS * (2 ** (retry_count - 1)),
                    MAX_RETRY_DELAY_SECONDS,
                )

                record.status = "failed"
                record.next_retry_at = datetime.now(timezone.utc) + timedelta(seconds=delay_seconds)
            else:
                record.status = "failed"
                record.next_retry_at = None

            await self.db.commit()
            return True

        except Exception:
            await self.db.rollback()
            raise
