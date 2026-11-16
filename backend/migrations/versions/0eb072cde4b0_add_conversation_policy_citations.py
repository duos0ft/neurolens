"""add conversation policy citations

Revision ID: 0eb072cde4b0
Revises: 72c9dbb6b2d7
Create Date: 2026-11-15 22:42:29.964821

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision: str = "0eb072cde4b0"
down_revision: Union[str, Sequence[str], None] = "72c9dbb6b2d7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "conversation_messages",
        sa.Column(
            "policy_citations",
            JSONB(),
            nullable=True,
        ),
        schema="public",
    )


def downgrade() -> None:
    op.drop_column(
        "conversation_messages",
        "policy_citations",
        schema="public",
    )
