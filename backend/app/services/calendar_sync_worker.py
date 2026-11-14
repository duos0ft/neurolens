import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.calendar_sync_record import CalendarSyncRecord


CALENDAR_SYNC_LEASE_SECONDS = 120
CALENDAR_SYNC_BATCH_SIZE = 20


@dataclass(frozen=True)
class ClaimedCalendarSyncJob:
    id: uuid.UUID
    integration_id: uuid.UUID
    source_type: str
    source_id: uuid.UUID
    operation: str
    revision: int
    attempt_id: uuid.UUID
    external_calendar_id: str | None
    external_event_id: str | None
    retry_count: int


class CalendarSyncWorker:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def claim_jobs(
        self,
        limit: int = CALENDAR_SYNC_BATCH_SIZE,
    ) -> list[ClaimedCalendarSyncJob]:
        if limit < 1 or limit > CALENDAR_SYNC_BATCH_SIZE:
            raise ValueError("Invalid calendar sync batch size")

        now = datetime.now(timezone.utc)
        lease_expires_at = now + timedelta(seconds=CALENDAR_SYNC_LEASE_SECONDS)

        try:
            query = (
                select(CalendarSyncRecord)
                .where(
                    or_(
                        CalendarSyncRecord.status == "pending",
                        and_(
                            CalendarSyncRecord.status == "failed",
                            CalendarSyncRecord.next_retry_at.is_not(None),
                            CalendarSyncRecord.next_retry_at <= now,
                        ),
                        and_(
                            CalendarSyncRecord.status == "syncing",
                            CalendarSyncRecord.lease_expires_at <= now,
                        ),
                    )
                )
                .order_by(
                    CalendarSyncRecord.created_at,
                    CalendarSyncRecord.id,
                )
                .limit(limit)
                .with_for_update(skip_locked=True)
            )

            records = (await self.db.scalars(query)).all()

            jobs: list[ClaimedCalendarSyncJob] = []

            for record in records:
                attempt_id = uuid.uuid4()

                record.status = "syncing"
                record.attempt_id = attempt_id
                record.lease_expires_at = lease_expires_at
                record.next_retry_at = None

                jobs.append(
                    ClaimedCalendarSyncJob(
                        id=record.id,
                        integration_id=record.integration_id,
                        source_type=record.source_type,
                        source_id=record.source_id,
                        operation=record.operation,
                        revision=record.revision,
                        attempt_id=attempt_id,
                        external_calendar_id=record.external_calendar_id,
                        external_event_id=record.external_event_id,
                        retry_count=record.retry_count,
                    )
                )

            await self.db.commit()

            return jobs

        except Exception:
            await self.db.rollback()
            raise
