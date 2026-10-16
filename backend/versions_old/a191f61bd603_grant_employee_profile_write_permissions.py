"""grant employee profile write permissions

Revision ID: a191f61bd603
Revises: 87a9f862d2ec
Create Date: 2026-10-17 00:15:52.967369

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a191f61bd603"
down_revision: Union[str, Sequence[str], None] = "87a9f862d2ec"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        GRANT SELECT, INSERT, UPDATE
        ON TABLE public.employee_profiles
        TO neurolens_admin
        """
    )


def downgrade() -> None:
    op.execute(
        """
        REVOKE INSERT, UPDATE
        ON TABLE public.employee_profiles
        FROM neurolens_admin
        """
    )
