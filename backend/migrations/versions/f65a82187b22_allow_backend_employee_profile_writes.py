"""allow backend employee profile writes

Revision ID: f65a82187b22
Revises: a191f61bd603
Create Date: 2026-10-17 00:20:07.980798

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f65a82187b22"
down_revision: Union[str, Sequence[str], None] = "a191f61bd603"
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

    op.execute(
        """
        CREATE POLICY "Backend inserts employee profiles"
        ON public.employee_profiles
        FOR INSERT
        TO neurolens_admin
        WITH CHECK (true)
        """
    )

    op.execute(
        """
        CREATE POLICY "Backend updates employee profiles"
        ON public.employee_profiles
        FOR UPDATE
        TO neurolens_admin
        USING (true)
        WITH CHECK (true)
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP POLICY IF EXISTS "Backend updates employee profiles"
        ON public.employee_profiles
        """
    )

    op.execute(
        """
        DROP POLICY IF EXISTS "Backend inserts employee profiles"
        ON public.employee_profiles
        """
    )
