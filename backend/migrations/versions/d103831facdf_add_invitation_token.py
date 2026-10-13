"""add_invitation_token

Revision ID: d103831facdf
Revises: 98373ee41137
Create Date: 2026-10-13 22:06:46.924844

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d103831facdf"
down_revision: Union[str, Sequence[str], None] = "98373ee41137"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "employee_invitations",
        sa.Column(
            "token_hash",
            sa.Text(),
            nullable=False,
        ),
        schema="public",
    )

    op.create_unique_constraint(
        "employee_invitations_token_hash_key",
        "employee_invitations",
        ["token_hash"],
        schema="public",
    )


def downgrade() -> None:
    op.drop_constraint(
        "employee_invitations_token_hash_key",
        "employee_invitations",
        type_="unique",
        schema="public",
    )

    op.drop_column(
        "employee_invitations",
        "token_hash",
        schema="public",
    )
