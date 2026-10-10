import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Text, func
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
            "status IN ('active', 'suspended')",
            name="employees_status_check",
        ),
        {"schema": "public"},
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
    )

    auth0_user_id: Mapped[str | None] = mapped_column(
        Text,
        unique=True,
        nullable=True,
    )

    role: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="employee",
    )

    status: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="active",
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
