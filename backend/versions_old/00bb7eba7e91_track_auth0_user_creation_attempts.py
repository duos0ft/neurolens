"""track auth0 user creation attempts

Revision ID: 00bb7eba7e91
Revises: 28a00b9078f3
Create Date: 2026-10-13 22:27:52.966586

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "00bb7eba7e91"
down_revision: Union[str, Sequence[str], None] = "28a00b9078f3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "employee_invitations",
        sa.Column(
            "auth0_creation_started_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        schema="public",
    )


def downgrade() -> None:
    op.drop_column(
        "employee_invitations",
        "auth0_creation_started_at",
        schema="public",
    )
