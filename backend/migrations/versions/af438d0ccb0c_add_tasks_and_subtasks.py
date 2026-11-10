"""add tasks and subtasks

Revision ID: af438d0ccb0c
Revises: 93bfb2d1ae18
Create Date: 2026-11-08 20:37:20.819058

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "af438d0ccb0c"
down_revision: Union[str, Sequence[str], None] = "93bfb2d1ae18"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tasks",
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "employee_id",
            sa.UUID(),
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
            "status",
            sa.Text(),
            server_default=sa.text("'todo'"),
            nullable=False,
        ),
        sa.Column(
            "priority",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "due_date",
            sa.Date(),
            nullable=True,
        ),
        sa.Column(
            "source_message_id",
            sa.UUID(),
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
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "completed_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.CheckConstraint(
            "status IN ('todo', 'in_progress', 'completed')",
            name="tasks_status_check",
        ),
        sa.CheckConstraint(
            "priority IS NULL OR priority IN ('low', 'medium', 'high')",
            name="tasks_priority_check",
        ),
        sa.CheckConstraint(
            "source_suggestion_index IS NULL OR source_suggestion_index >= 0",
            name="tasks_source_suggestion_index_check",
        ),
        sa.ForeignKeyConstraint(
            ["employee_id"],
            ["public.employees.user_id"],
            name="tasks_employee_id_fkey",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["source_message_id"],
            ["public.conversation_messages.id"],
            name="tasks_source_message_id_fkey",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint(
            "id",
            name="tasks_pkey",
        ),
        sa.UniqueConstraint(
            "employee_id",
            "source_message_id",
            "source_suggestion_index",
            name="tasks_employee_source_suggestion_unique",
        ),
        schema="public",
    )

    op.create_index(
        "ix_public_tasks_employee_id",
        "tasks",
        ["employee_id"],
        unique=False,
        schema="public",
    )

    op.create_index(
        "ix_public_tasks_source_message_id",
        "tasks",
        ["source_message_id"],
        unique=False,
        schema="public",
    )

    op.create_table(
        "subtasks",
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "task_id",
            sa.UUID(),
            nullable=False,
        ),
        sa.Column(
            "title",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "completed",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column(
            "sort_order",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "sort_order >= 0",
            name="subtasks_sort_order_check",
        ),
        sa.ForeignKeyConstraint(
            ["task_id"],
            ["public.tasks.id"],
            name="subtasks_task_id_fkey",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "id",
            name="subtasks_pkey",
        ),
        sa.UniqueConstraint(
            "task_id",
            "sort_order",
            name="subtasks_task_sort_order_unique",
        ),
        schema="public",
    )

    op.create_index(
        "ix_public_subtasks_task_id",
        "subtasks",
        ["task_id"],
        unique=False,
        schema="public",
    )


def downgrade() -> None:
    op.drop_index(
        "ix_public_subtasks_task_id",
        table_name="subtasks",
        schema="public",
    )

    op.drop_table(
        "subtasks",
        schema="public",
    )

    op.drop_index(
        "ix_public_tasks_source_message_id",
        table_name="tasks",
        schema="public",
    )

    op.drop_index(
        "ix_public_tasks_employee_id",
        table_name="tasks",
        schema="public",
    )

    op.drop_table(
        "tasks",
        schema="public",
    )
