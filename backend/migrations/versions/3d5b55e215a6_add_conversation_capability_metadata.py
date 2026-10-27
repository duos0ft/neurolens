"""add conversation capability metadata

Revision ID: 3d5b55e215a6
Revises: b690ce05e392
Create Date: 2026-10-27 23:29:53.520021

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision: str = "3d5b55e215a6"
down_revision: Union[str, Sequence[str], None] = "b690ce05e392"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "conversation_messages",
        sa.Column(
            "capability_metadata",
            JSONB(),
            nullable=True,
        ),
        schema="public",
    )


def downgrade() -> None:
    op.drop_column(
        "conversation_messages",
        "capability_metadata",
        schema="public",
    )
