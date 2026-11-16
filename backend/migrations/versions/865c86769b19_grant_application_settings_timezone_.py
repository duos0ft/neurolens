"""grant application settings timezone update

Revision ID: 865c86769b19
Revises: 7ba688e89423
Create Date: 2026-11-12 22:11:58.377417

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "865c86769b19"
down_revision: Union[str, Sequence[str], None] = "7ba688e89423"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        GRANT UPDATE (default_timezone)
        ON TABLE public.application_settings
        TO neurolens_admin
        """
    )


def downgrade() -> None:
    op.execute(
        """
        REVOKE UPDATE (default_timezone)
        ON TABLE public.application_settings
        FROM neurolens_admin
        """
    )
