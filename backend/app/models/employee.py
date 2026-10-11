import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Index, Text, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Employee(Base):
    __tablename__ = "employees"

    __table_args__ = (
        CheckConstraint(
            "role IN ('admin', 'employee')",
            name="employees_role_check",
        ),
        CheckConstraint(
            "status IN ('invited', 'active', 'suspended')",
            name="employees_status_check",
        ),
        Index(
            "employees_email_lower_idx",
            text("lower(email)"),
            unique=True,
        ),
        {"schema": "public"},
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    auth0_user_id: Mapped[str | None] = mapped_column(
        Text,
        unique=True,
        nullable=True,
    )

    email: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    role: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        server_default="employee",
    )

    status: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        server_default="invited",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
