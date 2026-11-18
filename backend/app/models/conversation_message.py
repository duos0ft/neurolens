import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ConversationMessage(Base):
    __tablename__ = "conversation_messages"

    __table_args__ = (
        CheckConstraint(
            "role IN ('user', 'assistant')",
            name="conversation_messages_role_check",
        ),
        CheckConstraint(
            "sequence_number > 0",
            name="conversation_messages_sequence_positive_check",
        ),
        UniqueConstraint(
            "conversation_id",
            "sequence_number",
            name="conversation_messages_sequence_unique",
        ),
        {"schema": "public"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "public.conversations.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    sequence_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    role: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    model: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    capability_metadata: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    task_suggestions: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    calendar_suggestions: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    clarifications: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    policy_citations: Mapped[list[dict] | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    sentiment_analysis: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )
