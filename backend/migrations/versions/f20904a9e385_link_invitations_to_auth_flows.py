"""link invitations to auth flows

Revision ID: f20904a9e385
Revises: 0001_initial_neurolens
Create Date: 2026-10-18 00:12:55.950923

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f20904a9e385"
down_revision: Union[str, Sequence[str], None] = "0001_initial_neurolens"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "auth_flows",
        sa.Column(
            "invitation_id",
            sa.UUID(),
            nullable=True,
        ),
        schema="public",
    )

    op.create_foreign_key(
        "auth_flows_invitation_id_fkey",
        "auth_flows",
        "employee_invitations",
        ["invitation_id"],
        ["id"],
        source_schema="public",
        referent_schema="public",
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(
        "auth_flows_invitation_id_fkey",
        "auth_flows",
        type_="foreignkey",
        schema="public",
    )

    op.drop_column(
        "auth_flows",
        "invitation_id",
        schema="public",
    )
