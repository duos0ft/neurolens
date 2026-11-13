import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class CalendarOAuthFlow(Base):
    __tablename__ = "calendar_oauth_flows"

    __table_args__ = (
        CheckConstraint(
            "provider IN ('google', 'microsoft')",
            name="calendar_oauth_flows_provider_check",
        ),
        CheckConstraint(
            "expires_at > created_at",
            name="calendar_oauth_flows_valid_expiry",
        ),
        Index(
            "calendar_oauth_flows_expires_at_idx",
            "expires_at",
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
    )

    provider: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    state_hash: Mapped[str] = mapped_column(
        Text,
        unique=True,
        nullable=False,
    )

    browser_nonce_hash: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    session_hash: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    code_verifier: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    return_path: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        server_default="/app/profile",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    consumed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
