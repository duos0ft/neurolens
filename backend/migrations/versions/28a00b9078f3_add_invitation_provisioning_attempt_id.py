"""add invitation provisioning attempt id

Revision ID: 28a00b9078f3
Revises: d103831facdf
Create Date: 2026-10-13 22:14:19.020161

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "28a00b9078f3"
down_revision: Union[str, Sequence[str], None] = "d103831facdf"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "employee_invitations",
        sa.Column(
            "provisioning_attempt_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        schema="public",
    )


def downgrade() -> None:
    op.drop_column(
        "employee_invitations",
        "provisioning_attempt_id",
        schema="public",
    )
