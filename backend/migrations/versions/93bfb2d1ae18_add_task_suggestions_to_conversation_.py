"""add task suggestions to conversation messages

Revision ID: 93bfb2d1ae18
Revises: 3d5b55e215a6
Create Date: 2026-11-03 00:25:03.349538

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "93bfb2d1ae18"
down_revision: Union[str, Sequence[str], None] = "3d5b55e215a6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "conversation_messages",
        sa.Column(
            "task_suggestions",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        schema="public",
    )


def downgrade() -> None:
    op.drop_column(
        "conversation_messages",
        "task_suggestions",
        schema="public",
    )
