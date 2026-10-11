import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class EmployeeProfile(Base):
    __tablename__ = "employee_profiles"

    __table_args__ = (
        CheckConstraint(
            "directness IN ('low', 'balanced', 'high')",
            name="employee_profiles_directness_check",
        ),
        CheckConstraint(
            "response_length IN ('short', 'medium', 'detailed')",
            name="employee_profiles_response_length_check",
        ),
        {"schema": "public"},
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "public.employees.user_id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    )

    display_name: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    timezone: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        server_default="UTC",
    )

    directness: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        server_default="balanced",
    )

    response_length: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        server_default="medium",
    )

    highlight_ambiguity: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="true",
    )

    step_by_step_guidance: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="true",
    )

    always_show_next_step: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="true",
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
