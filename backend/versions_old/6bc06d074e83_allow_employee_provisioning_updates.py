"""allow_employee_provisioning_updates

Revision ID: 6bc06d074e83
Revises: 1bb1edc83d80
Create Date: 2026-10-12 23:40:48.689580

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "6bc06d074e83"
down_revision: Union[str, Sequence[str], None] = "1bb1edc83d80"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        GRANT UPDATE (
            auth0_user_id,
            provisioning_status
        )
        ON public.employees
        TO neurolens_admin;
    """)

    op.execute("""
        CREATE POLICY "Backend updates employee provisioning"
        ON public.employees
        FOR UPDATE
        TO neurolens_admin
        USING (true)
        WITH CHECK (true);
    """)


def downgrade() -> None:
    op.execute("""
        DROP POLICY IF EXISTS
            "Backend updates employee provisioning"
        ON public.employees;
    """)

    op.execute("""
        REVOKE UPDATE (
            auth0_user_id,
            provisioning_status
        )
        ON public.employees
        FROM neurolens_admin;
    """)
