"""Add employee email.

Revision ID: ed57f51ff1fc
Revises: 9128aba1a70a
Create Date: 2026-10-12
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "ed57f51ff1fc"
down_revision: Union[str, Sequence[str], None] = "9128aba1a70a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "employees",
        sa.Column(
            "email",
            sa.Text(),
            nullable=True,
        ),
        schema="public",
    )

    op.create_index(
        "employees_email_lower_idx",
        "employees",
        [sa.text("lower(email)")],
        unique=True,
        schema="public",
    )


def downgrade() -> None:
    op.drop_index(
        "employees_email_lower_idx",
        table_name="employees",
        schema="public",
    )

    op.drop_column(
        "employees",
        "email",
        schema="public",
    )
