"""add deletion of tasks

Revision ID: 1366dafc2e42
Revises: 661688ad32c5
Create Date: 2026-11-11 21:46:05.572359

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "1366dafc2e42"
down_revision: Union[str, Sequence[str], None] = "661688ad32c5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "tasks",
        sa.Column(
            "archived_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        schema="public",
    )

    op.add_column(
        "tasks",
        sa.Column(
            "deleted_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        schema="public",
    )


def downgrade() -> None:
    op.drop_column(
        "tasks",
        "deleted_at",
        schema="public",
    )

    op.drop_column(
        "tasks",
        "archived_at",
        schema="public",
    )
