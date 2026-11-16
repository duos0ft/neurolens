"""allow policy chunk lifecycle operations

Revision ID: ba4f29455ff5
Revises: 0ea915f8f900
Create Date: 2026-11-15 21:16:52.405489

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "ba4f29455ff5"
down_revision: Union[str, Sequence[str], None] = "0ea915f8f900"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("GRANT DELETE ON TABLE public.policy_chunks TO neurolens_admin")

    op.execute(
        """
        CREATE POLICY policy_chunks_delete_runtime_policy
        ON public.policy_chunks
        FOR DELETE
        TO neurolens_admin
        USING (true)
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP POLICY IF EXISTS policy_chunks_delete_runtime_policy
        ON public.policy_chunks
        """
    )

    op.execute("REVOKE DELETE ON TABLE public.policy_chunks FROM neurolens_admin")
