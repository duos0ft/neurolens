"""add conversation message clarifications

Revision ID: 47e6fa4eba9a
Revises: c4bc9c9363c8
Create Date: 2026-11-13 00:55:27.931235

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision: str = "47e6fa4eba9a"
down_revision: Union[str, Sequence[str], None] = "c4bc9c9363c8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "conversation_messages",
        sa.Column(
            "clarifications",
            JSONB(),
            nullable=True,
        ),
        schema="public",
    )


def downgrade() -> None:
    op.drop_column(
        "conversation_messages",
        "clarifications",
        schema="public",
    )
