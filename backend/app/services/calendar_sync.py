import uuid

from sqlalchemy import case, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.calendar_integration import CalendarIntegration
from app.models.calendar_sync_record import CalendarSyncRecord


class CalendarSyncService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def enqueue_upsert(
        self,
        employee_id: uuid.UUID,
        source_type: str,
        source_id: uuid.UUID,
    ) -> None:
        await self._enqueue(
            employee_id=employee_id,
            source_type=source_type,
            source_id=source_id,
            operation="upsert",
        )

    async def enqueue_delete(
        self,
        employee_id: uuid.UUID,
        source_type: str,
        source_id: uuid.UUID,
    ) -> None:
        await self._enqueue(
            employee_id=employee_id,
            source_type=source_type,
            source_id=source_id,
            operation="delete",
        )

    async def _enqueue(
        self,
        employee_id: uuid.UUID,
        source_type: str,
        source_id: uuid.UUID,
        operation: str,
    ) -> None:
        if source_type not in ("task", "calendar_event"):
            raise ValueError("Unsupported calendar sync source")

        if operation not in ("upsert", "delete"):
            raise ValueError("Unsupported calendar sync operation")

        integration_ids = (
            await self.db.scalars(
                select(CalendarIntegration.id).where(
                    CalendarIntegration.employee_id == employee_id,
                    CalendarIntegration.provider == "google",
                )
            )
        ).all()

        for integration_id in integration_ids:
            if operation == "upsert":
                await self._upsert_record(
                    integration_id,
                    source_type,
                    source_id,
                )
            else:
                await self._delete_record(
                    integration_id,
                    source_type,
                    source_id,
                )

    @staticmethod
    def _next_status():
        return case(
            (
                CalendarSyncRecord.status == "syncing",
                "syncing",
            ),
            else_="pending",
        )

    @staticmethod
    def _next_attempt():
        return case(
            (
                CalendarSyncRecord.status == "syncing",
                CalendarSyncRecord.attempt_id,
            ),
            else_=None,
        )

    @staticmethod
    def _next_lease():
        return case(
            (
                CalendarSyncRecord.status == "syncing",
                CalendarSyncRecord.lease_expires_at,
            ),
            else_=None,
        )

    async def _upsert_record(
        self,
        integration_id: uuid.UUID,
        source_type: str,
        source_id: uuid.UUID,
    ) -> None:
        statement = insert(CalendarSyncRecord).values(
            integration_id=integration_id,
            source_type=source_type,
            source_id=source_id,
            operation="upsert",
            status="pending",
            revision=1,
            retry_count=0,
        )

        statement = statement.on_conflict_do_update(
            constraint="calendar_sync_records_source_unique",
            set_={
                "operation": "upsert",
                "revision": CalendarSyncRecord.revision + 1,
                "status": self._next_status(),
                "retry_count": 0,
                "next_retry_at": None,
                "last_error_code": None,
                "attempt_id": self._next_attempt(),
                "lease_expires_at": self._next_lease(),
            },
        )

        await self.db.execute(statement)

    async def _delete_record(
        self,
        integration_id: uuid.UUID,
        source_type: str,
        source_id: uuid.UUID,
    ) -> None:
        statement = (
            update(CalendarSyncRecord)
            .where(
                CalendarSyncRecord.integration_id == integration_id,
                CalendarSyncRecord.source_type == source_type,
                CalendarSyncRecord.source_id == source_id,
            )
            .values(
                operation="delete",
                revision=CalendarSyncRecord.revision + 1,
                status=self._next_status(),
                retry_count=0,
                next_retry_at=None,
                last_error_code=None,
                attempt_id=self._next_attempt(),
                lease_expires_at=self._next_lease(),
            )
        )

        await self.db.execute(statement)
