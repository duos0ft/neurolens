import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Index,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ContactPerson(Base):
    __tablename__ = "contact_persons"

    __table_args__ = (
        Index(
            "ix_contact_persons_active_responsibility",
            "responsibility",
            postgresql_where=text("is_active = true"),
        ),
        Index(
            "uq_contact_persons_primary_responsibility",
            "responsibility",
            unique=True,
            postgresql_where=text("is_primary = true AND is_active = true"),
        ),
        CheckConstraint(
            "btrim(name) <> ''",
            name="contact_persons_name_check",
        ),
        CheckConstraint(
            "btrim(email) <> ''",
            name="contact_persons_email_check",
        ),
        CheckConstraint(
            "length(btrim(responsibility)) > 0",
            name="contact_persons_responsibility_check",
        ),
        UniqueConstraint(
            "email",
            name="contact_persons_email_unique",
        ),
        {"schema": "public"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    name: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    job_title: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    email: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    department: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    responsibility: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    is_primary: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="false",
    )

    is_active: Mapped[bool] = mapped_column(
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
