"""add task deadline time and timezone

Revision ID: c4bc9c9363c8
Revises: 865c86769b19
Create Date: 2026-11-12 22:50:41.049107

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c4bc9c9363c8"
down_revision: Union[str, Sequence[str], None] = "865c86769b19"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "tasks",
        sa.Column(
            "due_time",
            sa.Time(timezone=False),
            nullable=True,
        ),
        schema="public",
    )

    op.add_column(
        "tasks",
        sa.Column(
            "due_timezone",
            sa.Text(),
            nullable=True,
        ),
        schema="public",
    )

    op.create_check_constraint(
        "tasks_due_time_timezone_check",
        "tasks",
        """
        (
            due_time IS NULL
            AND due_timezone IS NULL
        )
        OR
        (
            due_date IS NOT NULL
            AND due_time IS NOT NULL
            AND due_timezone IS NOT NULL
        )
        """,
        schema="public",
    )

    # The application role needs permission to write the
    # newly introduced deadline columns.
    op.execute(
        """
        GRANT UPDATE (due_time, due_timezone)
        ON TABLE public.tasks
        TO neurolens_admin
        """
    )


def downgrade() -> None:
    op.execute(
        """
        REVOKE UPDATE (due_time, due_timezone)
        ON TABLE public.tasks
        FROM neurolens_admin
        """
    )

    op.drop_constraint(
        "tasks_due_time_timezone_check",
        "tasks",
        type_="check",
        schema="public",
    )

    op.drop_column(
        "tasks",
        "due_timezone",
        schema="public",
    )

    op.drop_column(
        "tasks",
        "due_time",
        schema="public",
    )