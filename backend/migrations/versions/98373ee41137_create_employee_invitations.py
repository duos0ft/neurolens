"""create_employee_invitations

Revision ID: 98373ee41137
Revises: 6bc06d074e83
Create Date: 2026-10-13 21:57:48.439503

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "98373ee41137"
down_revision: Union[str, Sequence[str], None] = "6bc06d074e83"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "employee_invitations",
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "employee_id",
            sa.UUID(),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Text(),
            server_default="pending",
            nullable=False,
        ),
        sa.Column(
            "attempt_count",
            sa.Integer(),
            server_default="0",
            nullable=False,
        ),
        sa.Column(
            "provisioning_started_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "last_error_code",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "expires_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "accepted_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "cancelled_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "employee_id",
            name="employee_invitations_employee_id_key",
        ),
        sa.ForeignKeyConstraint(
            ["employee_id"],
            ["public.employees.user_id"],
            ondelete="CASCADE",
        ),
        sa.CheckConstraint(
            "status IN ("
            "'pending', 'provisioning', 'ready', "
            "'accepted', 'failed', 'expired', 'cancelled'"
            ")",
            name="employee_invitations_status_check",
        ),
        sa.CheckConstraint(
            "attempt_count >= 0",
            name="employee_invitations_attempt_count_check",
        ),
        sa.CheckConstraint(
            "accepted_at IS NULL OR status = 'accepted'",
            name="employee_invitations_accepted_at_check",
        ),
        sa.CheckConstraint(
            "cancelled_at IS NULL OR status = 'cancelled'",
            name="employee_invitations_cancelled_at_check",
        ),
        schema="public",
    )

    op.create_index(
        "employee_invitations_status_idx",
        "employee_invitations",
        ["status"],
        schema="public",
    )

    op.create_index(
        "employee_invitations_expires_at_idx",
        "employee_invitations",
        ["expires_at"],
        schema="public",
    )

    op.execute("""
               CREATE TRIGGER employee_invitations_updated_at
                   BEFORE UPDATE ON public.employee_invitations
                   FOR EACH ROW
                   EXECUTE FUNCTION public.set_updated_at();
               """)

    op.execute("""
               ALTER TABLE public.employee_invitations
                   ENABLE ROW LEVEL SECURITY;
               """)

    op.execute("""
        REVOKE ALL ON public.employee_invitations
        FROM PUBLIC;
    """)

    op.execute("""
        GRANT SELECT, INSERT, UPDATE
        ON public.employee_invitations
        TO neurolens_admin;
    """)

    op.execute("""
        CREATE POLICY "Backend manages employee invitations"
        ON public.employee_invitations
        FOR ALL
        TO neurolens_admin
        USING (true)
        WITH CHECK (true);
    """)


def downgrade() -> None:
    op.execute("""
        DROP POLICY IF EXISTS
            "Backend manages employee invitations"
        ON public.employee_invitations;
    """)

    op.execute("""
        REVOKE SELECT, INSERT, UPDATE
        ON public.employee_invitations
        FROM neurolens_admin;
    """)

    op.execute("""
        DROP TRIGGER IF EXISTS
            employee_invitations_updated_at
        ON public.employee_invitations;
    """)

    op.drop_index(
        "employee_invitations_expires_at_idx",
        table_name="employee_invitations",
        schema="public",
    )

    op.drop_index(
        "employee_invitations_status_idx",
        table_name="employee_invitations",
        schema="public",
    )

    op.drop_table(
        "employee_invitations",
        schema="public",
    )
