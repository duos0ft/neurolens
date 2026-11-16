"""grant pgvector schema usage to runtime role

Revision ID: 72c9dbb6b2d7
Revises: ba4f29455ff5
Create Date: 2026-11-15 22:30:00.749298

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "72c9dbb6b2d7"
down_revision: Union[str, Sequence[str], None] = "ba4f29455ff5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("GRANT USAGE ON SCHEMA extensions TO neurolens_admin")


def downgrade() -> None:
    op.execute("REVOKE USAGE ON SCHEMA extensions FROM neurolens_admin")
