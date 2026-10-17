import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Index,
    Text,
    func,
    text,
    ForeignKey,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class AuthFlow(Base):
    __tablename__ = "auth_flows"

    __table_args__ = (
        CheckConstraint(
            "expires_at > created_at",
            name="auth_flows_valid_expiry",
        ),
        Index(
            "auth_flows_expires_at_idx",
            "expires_at",
        ),
        {"schema": "public"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    invitation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "public.employee_invitations.id",
            ondelete="SET NULL",
        ),
        nullable=True,
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

    oidc_nonce: Mapped[str] = mapped_column(
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
        server_default="/app",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    consumed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
