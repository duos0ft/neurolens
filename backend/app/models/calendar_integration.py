import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    LargeBinary,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class CalendarProvider(StrEnum):
    GOOGLE = "google"
    MICROSOFT = "microsoft"


class CalendarIntegration(Base):
    __tablename__ = "calendar_integrations"

    __table_args__ = (
        CheckConstraint(
            "provider IN ('google', 'microsoft')",
            name="calendar_integrations_provider_check",
        ),
        UniqueConstraint(
            "employee_id",
            "provider",
            name="calendar_integrations_employee_provider_unique",
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

    provider: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    provider_account_id: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    account_email: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    encrypted_refresh_token: Mapped[bytes] = mapped_column(
        LargeBinary,
        nullable=False,
    )

    scopes: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    connected_at: Mapped[datetime] = mapped_column(
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
