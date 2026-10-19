from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Integer,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ApplicationSettings(Base):
    __tablename__ = "application_settings"

    __table_args__ = (
        CheckConstraint(
            "id = 1",
            name="application_settings_singleton_check",
        ),
        CheckConstraint(
            "organization_name <> ''",
            name="application_settings_organization_name_check",
        ),
        {"schema": "public"},
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    organization_name: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        server_default="NeuroLens",
    )

    enable_task_assistance: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="true",
    )

    enable_policy_assistance: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="true",
    )

    enable_sentiment_analysis: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="false",
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
