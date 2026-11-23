"""fix calendar integration delete permissions

Revision ID: 86f329af4555
Revises: 7475e451fe4f
Create Date: 2026-11-23 13:21:27.780856

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "86f329af4555"
down_revision: Union[str, Sequence[str], None] = "7475e451fe4f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("GRANT DELETE ON TABLE public.calendar_integrations TO neurolens_admin")

    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_policies
                WHERE schemaname = 'public'
                  AND tablename = 'calendar_integrations'
                  AND policyname = 'calendar_integrations_delete_runtime_policy'
            ) THEN
                CREATE POLICY calendar_integrations_delete_runtime_policy
                ON public.calendar_integrations
                FOR DELETE
                TO neurolens_admin
                USING (true);
            END IF;
        END
        $$;
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP POLICY IF EXISTS calendar_integrations_delete_runtime_policy
        ON public.calendar_integrations
        """
    )

    op.execute("REVOKE DELETE ON TABLE public.calendar_integrations FROM neurolens_admin")