"""add employee organizational fields

Revision ID: 87a9f862d2ec
Revises: ca4e8dd4caab
Create Date: 2026-10-14 00:24:31.797193

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "87a9f862d2ec"
down_revision: Union[str, Sequence[str], None] = "ca4e8dd4caab"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "employee_profiles",
        sa.Column("job_title", sa.Text(), nullable=True),
        schema="public",
    )

    op.add_column(
        "employee_profiles",
        sa.Column("department", sa.Text(), nullable=True),
        schema="public",
    )

    op.add_column(
        "employee_profiles",
        sa.Column("team", sa.Text(), nullable=True),
        schema="public",
    )


def downgrade() -> None:
    op.drop_column("employee_profiles", "team", schema="public")
    op.drop_column("employee_profiles", "department", schema="public")
    op.drop_column("employee_profiles", "job_title", schema="public")
