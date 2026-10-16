"""add_employee_provisioning_status

Revision ID: 1bb1edc83d80
Revises: 695a1e53def4
Create Date: 2026-10-12 23:38:04.391317

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "1bb1edc83d80"
down_revision: Union[str, Sequence[str], None] = "695a1e53def4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "employees",
        sa.Column(
            "provisioning_status",
            sa.Text(),
            nullable=False,
            server_default="pending",
        ),
        schema="public",
    )

    op.create_check_constraint(
        "employees_provisioning_status_check",
        "employees",
        "provisioning_status IN ('pending', 'completed', 'failed')",
        schema="public",
    )

    op.execute("""
               UPDATE public.employees
               SET provisioning_status = 'completed'
               WHERE auth0_user_id IS NOT NULL;
               """)


def downgrade() -> None:
    op.drop_constraint(
        "employees_provisioning_status_check",
        "employees",
        type_="check",
        schema="public",
    )

    op.drop_column(
        "employees",
        "provisioning_status",
        schema="public",
    )
