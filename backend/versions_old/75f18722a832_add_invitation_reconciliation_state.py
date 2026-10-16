"""add invitation reconciliation state

Revision ID: 75f18722a832
Revises: 00bb7eba7e91
Create Date: 2026-10-13 22:32:56.820406

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "75f18722a832"
down_revision: Union[str, Sequence[str], None] = "00bb7eba7e91"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint(
        "employee_invitations_status_check",
        "employee_invitations",
        type_="check",
        schema="public",
    )

    op.create_check_constraint(
        "employee_invitations_status_check",
        "employee_invitations",
        "status IN ("
        "'pending', "
        "'provisioning', "
        "'reconciliation_required', "
        "'ready', "
        "'accepted', "
        "'failed', "
        "'expired', "
        "'cancelled'"
        ")",
        schema="public",
    )


def downgrade() -> None:
    op.drop_constraint(
        "employee_invitations_status_check",
        "employee_invitations",
        type_="check",
        schema="public",
    )

    op.create_check_constraint(
        "employee_invitations_status_check",
        "employee_invitations",
        "status IN ("
        "'pending', "
        "'provisioning', "
        "'ready', "
        "'accepted', "
        "'failed', "
        "'expired', "
        "'cancelled'"
        ")",
        schema="public",
    )
