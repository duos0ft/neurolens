import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class CalendarSyncRecord(Base):
    __tablename__ = "calendar_sync_records"

    __table_args__ = (
        CheckConstraint(
            "source_type IN ('task', 'calendar_event')",
            name="calendar_sync_records_source_type_check",
        ),
        CheckConstraint(
            "status IN ('pending', 'syncing', 'synced', 'failed')",
            name="calendar_sync_records_status_check",
        ),
        CheckConstraint(
            "retry_count >= 0",
            name="calendar_sync_records_retry_count_check",
        ),
        CheckConstraint(
            "operation IN ('upsert', 'delete')",
            name="calendar_sync_records_operation_check",
        ),
        CheckConstraint(
            "revision >= 1",
            name="calendar_sync_records_revision_check",
        ),
        UniqueConstraint(
            "integration_id",
            "source_type",
            "source_id",
            name="calendar_sync_records_source_unique",
        ),
        Index(
            "calendar_sync_records_pending_idx",
            "status",
            "next_retry_at",
        ),
        Index(
            "calendar_sync_records_lease_idx",
            "status",
            "lease_expires_at",
        ),
        {"schema": "public"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    integration_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "public.calendar_integrations.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    source_type: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
    )

    external_calendar_id: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    external_event_id: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        server_default="pending",
    )

    operation: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        server_default="upsert",
    )

    retry_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default="0",
    )

    next_retry_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    revision: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default="1",
    )

    attempt_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )

    lease_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    last_synced_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    last_error_code: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
