"""add email outbox delivery ownership

Revision ID: 400d6732fec8
Revises: 67180e3f7e88
Create Date: 2026-10-13 23:29:29.341249

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "400d6732fec8"
down_revision: Union[str, Sequence[str], None] = "67180e3f7e88"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "email_outbox",
        sa.Column(
            "delivery_attempt_id",
            sa.UUID(),
            nullable=True,
        ),
        schema="public",
    )

    op.add_column(
        "email_outbox",
        sa.Column(
            "delivery_started_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        schema="public",
    )


def downgrade() -> None:
    op.drop_column(
        "email_outbox",
        "delivery_started_at",
        schema="public",
    )

    op.drop_column(
        "email_outbox",
        "delivery_attempt_id",
        schema="public",
    )
