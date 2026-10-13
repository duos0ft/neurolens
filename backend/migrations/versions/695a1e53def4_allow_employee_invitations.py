"""allow_employee_invitations

Revision ID: 695a1e53def4
Revises: ed57f51ff1fc
Create Date: 2026-10-12 23:30:21.402116

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "695a1e53def4"
down_revision: Union[str, Sequence[str], None] = "ed57f51ff1fc"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        GRANT INSERT ON public.employees
        TO neurolens_admin;
    """)

    op.execute("""
        CREATE POLICY "Backend creates employees"
        ON public.employees
        FOR INSERT
        TO neurolens_admin
        WITH CHECK (true);
    """)


def downgrade() -> None:
    op.execute("""
        DROP POLICY IF EXISTS "Backend creates employees"
        ON public.employees;
    """)

    op.execute("""
        REVOKE INSERT ON public.employees
        FROM neurolens_admin;
    """)
