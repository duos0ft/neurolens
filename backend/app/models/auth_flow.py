import uuid
from datetime import datetime
from app.models.base import Base
from sqlalchemy import DateTime, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column


class AuthFlow(Base):
    __tablename__ = "auth_flows"
    __table_args__ = {"schema": "public"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
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
        default="/app",
        nullable=False,
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