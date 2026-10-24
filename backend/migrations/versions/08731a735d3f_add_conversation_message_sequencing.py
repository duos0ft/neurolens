"""add conversation message sequencing

Revision ID: 08731a735d3f
Revises: 2257769c3390
Create Date: 2026-10-24 13:37:39.837736

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "08731a735d3f"
down_revision: Union[str, Sequence[str], None] = "2257769c3390"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "conversation_messages",
        sa.Column(
            "sequence_number",
            sa.Integer(),
            nullable=False,
        ),
        schema="public",
    )

    op.create_check_constraint(
        "conversation_messages_sequence_positive_check",
        "conversation_messages",
        "sequence_number > 0",
        schema="public",
    )

    op.create_unique_constraint(
        "conversation_messages_sequence_unique",
        "conversation_messages",
        ["conversation_id", "sequence_number"],
        schema="public",
    )


def downgrade() -> None:
    op.drop_constraint(
        "conversation_messages_sequence_unique",
        "conversation_messages",
        type_="unique",
        schema="public",
    )

    op.drop_constraint(
        "conversation_messages_sequence_positive_check",
        "conversation_messages",
        type_="check",
        schema="public",
    )

    op.drop_column(
        "conversation_messages",
        "sequence_number",
        schema="public",
    )
