"""create calendar events

Revision ID: 8adfaab3272b
Revises: 1366dafc2e42
Create Date: 2026-11-11 22:48:37.180054

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from migrations.runtime_access import RuntimeAccess, configure_runtime_access

# revision identifiers, used by Alembic.
revision: str = "8adfaab3272b"
down_revision: Union[str, Sequence[str], None] = "1366dafc2e42"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "calendar_events",
        sa.Column(
            "id",
            sa.UUID(),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "employee_id",
            sa.UUID(),
            sa.ForeignKey(
                "public.employees.user_id",
                ondelete="CASCADE",
            ),
            nullable=False,
        ),
        sa.Column(
            "title",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "description",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "event_type",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "all_day",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        sa.Column(
            "start_date",
            sa.Date(),
            nullable=True,
        ),
        sa.Column(
            "end_date",
            sa.Date(),
            nullable=True,
        ),
        sa.Column(
            "starts_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "ends_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "timezone",
            sa.Text(),
            nullable=False,
            server_default="UTC",
        ),
        sa.Column(
            "source_message_id",
            sa.UUID(),
            sa.ForeignKey(
                "public.conversation_messages.id",
                ondelete="SET NULL",
            ),
            nullable=True,
        ),
        sa.Column(
            "source_suggestion_index",
            sa.Integer(),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "event_type IN ('meeting', 'appointment', 'event', 'deadline')",
            name="calendar_events_event_type_check",
        ),
        sa.CheckConstraint(
            "source_suggestion_index IS NULL OR source_suggestion_index >= 0",
            name="calendar_events_source_suggestion_index_check",
        ),
        sa.CheckConstraint(
            "source_suggestion_index IS NULL OR source_message_id IS NOT NULL",
            name="calendar_events_source_suggestion_message_check",
        ),
        sa.CheckConstraint(
            """
            (
                all_day = true
                AND start_date IS NOT NULL
                AND end_date IS NOT NULL
                AND starts_at IS NULL
                AND ends_at IS NULL
                AND end_date > start_date
            )
            OR
            (
                all_day = false
                AND start_date IS NULL
                AND end_date IS NULL
                AND starts_at IS NOT NULL
                AND ends_at IS NOT NULL
                AND ends_at > starts_at
            )
            """,
            name="calendar_events_date_range_check",
        ),
        sa.UniqueConstraint(
            "employee_id",
            "source_message_id",
            "source_suggestion_index",
            name="calendar_events_employee_source_suggestion_unique",
        ),
        schema="public",
    )

    op.create_index(
        "ix_calendar_events_employee_id",
        "calendar_events",
        ["employee_id"],
        schema="public",
    )

    op.create_index(
        "ix_calendar_events_source_message_id",
        "calendar_events",
        ["source_message_id"],
        schema="public",
    )

    op.create_index(
        "ix_calendar_events_employee_start_date",
        "calendar_events",
        ["employee_id", "start_date"],
        schema="public",
    )

    op.create_index(
        "ix_calendar_events_employee_starts_at",
        "calendar_events",
        ["employee_id", "starts_at"],
        schema="public",
    )

    op.execute(
        """
        CREATE TRIGGER calendar_events_updated_at
            BEFORE UPDATE ON public.calendar_events
            FOR EACH ROW
            EXECUTE FUNCTION public.set_updated_at()
        """
    )

    configure_runtime_access(
        "calendar_events",
        RuntimeAccess.READ_WRITE,
        update_columns=(
            "title",
            "description",
            "event_type",
            "all_day",
            "start_date",
            "end_date",
            "starts_at",
            "ends_at",
            "timezone",
        ),
    )


def downgrade() -> None:
    op.execute(
        """
        DROP TRIGGER IF EXISTS calendar_events_updated_at
        ON public.calendar_events
        """
    )

    op.drop_index(
        "ix_calendar_events_employee_starts_at",
        table_name="calendar_events",
        schema="public",
    )

    op.drop_index(
        "ix_calendar_events_employee_start_date",
        table_name="calendar_events",
        schema="public",
    )

    op.drop_index(
        "ix_calendar_events_source_message_id",
        table_name="calendar_events",
        schema="public",
    )

    op.drop_index(
        "ix_calendar_events_employee_id",
        table_name="calendar_events",
        schema="public",
    )

    op.drop_table(
        "calendar_events",
        schema="public",
    )