"""allow employee activation

Revision ID: 26d35e61bdd4
Revises: f20904a9e385
Create Date: 2026-10-18 00:20:30.887489

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "26d35e61bdd4"
down_revision: Union[str, Sequence[str], None] = "f20904a9e385"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        GRANT UPDATE (status)
        ON TABLE public.employees
        TO neurolens_admin
        """
    )


def downgrade() -> None:
    op.execute(
        """
        REVOKE UPDATE (status)
        ON TABLE public.employees
        FROM neurolens_admin
        """
    )
