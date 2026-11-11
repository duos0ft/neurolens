import uuid
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class CalendarEvent(Base):
    __tablename__ = "calendar_events"

    __table_args__ = (
        CheckConstraint(
            "event_type IN ('meeting', 'appointment', 'event', 'deadline')",
            name="calendar_events_event_type_check",
        ),
        CheckConstraint(
            "source_suggestion_index IS NULL OR source_suggestion_index >= 0",
            name="calendar_events_source_suggestion_index_check",
        ),
        CheckConstraint(
            "source_suggestion_index IS NULL OR source_message_id IS NOT NULL",
            name="calendar_events_source_suggestion_message_check",
        ),
        CheckConstraint(
            """
            (
                all_day = true
                AND start_date IS NOT NULL
                AND end_date IS NOT NULL
                AND starts_at IS NULL
                AND ends_at IS NULL
                AND end_date > start_date
            )
            OR
            (
                all_day = false
                AND start_date IS NULL
                AND end_date IS NULL
                AND starts_at IS NOT NULL
                AND ends_at IS NOT NULL
                AND ends_at > starts_at
            )
            """,
            name="calendar_events_date_range_check",
        ),
        UniqueConstraint(
            "employee_id",
            "source_message_id",
            "source_suggestion_index",
            name="calendar_events_employee_source_suggestion_unique",
        ),
        {"schema": "public"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    employee_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "public.employees.user_id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    title: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    event_type: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    all_day: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("false"),
    )

    start_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    end_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    starts_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    ends_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    timezone: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        server_default=text("'UTC'"),
    )

    source_message_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "public.conversation_messages.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    source_suggestion_index: Mapped[int | None] = mapped_column(
        Integer,
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
        onupdate=func.now(),
    )
