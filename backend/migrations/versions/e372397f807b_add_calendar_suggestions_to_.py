"""add calendar suggestions to conversation messages

Revision ID: e372397f807b
Revises: 8adfaab3272b
Create Date: 2026-11-11 23:20:03.933265

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e372397f807b"
down_revision: Union[str, Sequence[str], None] = "8adfaab3272b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "conversation_messages",
        sa.Column(
            "calendar_suggestions",
            sa.dialects.postgresql.JSONB(),
            nullable=True,
        ),
        schema="public",
    )


def downgrade() -> None:
    op.drop_column(
        "conversation_messages",
        "calendar_suggestions",
        schema="public",
    )
