"""add conversation message sentiment analysis

Revision ID: 7475e451fe4f
Revises: 0eb072cde4b0
Create Date: 2026-11-18 21:13:31.254231

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision: str = "7475e451fe4f"
down_revision: Union[str, Sequence[str], None] = "0eb072cde4b0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "conversation_messages",
        sa.Column(
            "sentiment_analysis",
            JSONB(),
            nullable=True,
        ),
        schema="public",
    )


def downgrade() -> None:
    op.drop_column(
        "conversation_messages",
        "sentiment_analysis",
        schema="public",
    )
