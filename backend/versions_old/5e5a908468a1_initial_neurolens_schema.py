"""Initial NeuroLens database schema.

Revision ID: 5e5a908468a1
Revises:
Create Date: 2026-10-12
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# Revision identifiers
revision: str = "5e5a908468a1"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ---------------------------------------------------------
    # Employees
    # ---------------------------------------------------------

    op.create_table(
        "employees",
        sa.Column(
            "user_id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "auth0_user_id",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "role",
            sa.Text(),
            server_default="employee",
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Text(),
            server_default="invited",
            nullable=False,
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
        sa.PrimaryKeyConstraint("user_id"),
        sa.UniqueConstraint("auth0_user_id"),
        sa.CheckConstraint(
            "role IN ('admin', 'employee')",
            name="employees_role_check",
        ),
        sa.CheckConstraint(
            "status IN ('invited', 'active', 'suspended')",
            name="employees_status_check",
        ),
        schema="public",
    )

    # ---------------------------------------------------------
    # Employee Profiles
    # ---------------------------------------------------------

    op.create_table(
        "employee_profiles",
        sa.Column(
            "user_id",
            sa.UUID(),
            nullable=False,
        ),
        sa.Column(
            "display_name",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "timezone",
            sa.Text(),
            server_default="UTC",
            nullable=False,
        ),
        sa.Column(
            "directness",
            sa.Text(),
            server_default="balanced",
            nullable=False,
        ),
        sa.Column(
            "response_length",
            sa.Text(),
            server_default="medium",
            nullable=False,
        ),
        sa.Column(
            "highlight_ambiguity",
            sa.Boolean(),
            server_default=sa.true(),
            nullable=False,
        ),
        sa.Column(
            "step_by_step_guidance",
            sa.Boolean(),
            server_default=sa.true(),
            nullable=False,
        ),
        sa.Column(
            "always_show_next_step",
            sa.Boolean(),
            server_default=sa.true(),
            nullable=False,
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
        sa.PrimaryKeyConstraint("user_id"),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["public.employees.user_id"],
            ondelete="CASCADE",
        ),
        sa.CheckConstraint(
            "directness IN ('low', 'balanced', 'high')",
            name="employee_profiles_directness_check",
        ),
        sa.CheckConstraint(
            "response_length IN ('short', 'medium', 'detailed')",
            name="employee_profiles_response_length_check",
        ),
        schema="public",
    )

    # ---------------------------------------------------------
    # OAuth Flows
    # ---------------------------------------------------------

    op.create_table(
        "auth_flows",
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "state_hash",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "browser_nonce_hash",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "oidc_nonce",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "code_verifier",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "return_path",
            sa.Text(),
            server_default="/app",
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "expires_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "consumed_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("state_hash"),
        sa.CheckConstraint(
            "expires_at > created_at",
            name="auth_flows_valid_expiry",
        ),
        schema="public",
    )

    op.create_index(
        "auth_flows_expires_at_idx",
        "auth_flows",
        ["expires_at"],
        schema="public",
    )

    # ---------------------------------------------------------
    # Employee Sessions
    # ---------------------------------------------------------

    op.create_table(
        "employee_sessions",
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "session_hash",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "employee_id",
            sa.UUID(),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "last_active_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "expires_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "revoked_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("session_hash"),
        sa.ForeignKeyConstraint(
            ["employee_id"],
            ["public.employees.user_id"],
            ondelete="CASCADE",
        ),
        sa.CheckConstraint(
            "expires_at > created_at",
            name="employee_sessions_valid_expiry",
        ),
        schema="public",
    )

    op.create_index(
        "employee_sessions_employee_id_idx",
        "employee_sessions",
        ["employee_id"],
        schema="public",
    )

    op.create_index(
        "employee_sessions_expires_at_idx",
        "employee_sessions",
        ["expires_at"],
        schema="public",
    )

    # ---------------------------------------------------------
    # Updated-at trigger function
    # ---------------------------------------------------------

    op.execute(
        """
        CREATE FUNCTION public.set_updated_at()
            RETURNS trigger
            LANGUAGE plpgsql
        SET search_path = ''
        AS $$
        BEGIN
            NEW.updated_at = now();
        RETURN NEW;
        END;
        $$;
        """
    )

    # ---------------------------------------------------------
    # Updated-at triggers
    # ---------------------------------------------------------

    op.execute(
        """
        CREATE TRIGGER employees_updated_at
            BEFORE UPDATE ON public.employees
            FOR EACH ROW
            EXECUTE FUNCTION public.set_updated_at();
        """
    )

    op.execute(
        """
        CREATE TRIGGER employee_profiles_updated_at
            BEFORE UPDATE ON public.employee_profiles
            FOR EACH ROW
            EXECUTE FUNCTION public.set_updated_at();
        """
    )

    # ---------------------------------------------------------
    # Row Level Security
    # ---------------------------------------------------------

    op.execute("ALTER TABLE public.employees ENABLE ROW LEVEL SECURITY")

    op.execute("ALTER TABLE public.employee_profiles ENABLE ROW LEVEL SECURITY")

    op.execute("ALTER TABLE public.auth_flows ENABLE ROW LEVEL SECURITY")

    op.execute("ALTER TABLE public.employee_sessions ENABLE ROW LEVEL SECURITY")


def downgrade() -> None:
    # ---------------------------------------------------------
    # Triggers
    # ---------------------------------------------------------

    op.execute(
        """
        DROP TRIGGER IF EXISTS employee_profiles_updated_at
        ON public.employee_profiles;
        """
    )

    op.execute(
        """
        DROP TRIGGER IF EXISTS employees_updated_at
        ON public.employees;
        """
    )

    op.execute("DROP FUNCTION IF EXISTS public.set_updated_at()")

    # ---------------------------------------------------------
    # Indexes
    # ---------------------------------------------------------

    op.drop_index(
        "employee_sessions_expires_at_idx",
        table_name="employee_sessions",
        schema="public",
    )

    op.drop_index(
        "employee_sessions_employee_id_idx",
        table_name="employee_sessions",
        schema="public",
    )

    op.drop_index(
        "auth_flows_expires_at_idx",
        table_name="auth_flows",
        schema="public",
    )

    # ---------------------------------------------------------
    # Tables
    # ---------------------------------------------------------

    op.drop_table(
        "employee_sessions",
        schema="public",
    )

    op.drop_table(
        "employee_profiles",
        schema="public",
    )

    op.drop_table(
        "auth_flows",
        schema="public",
    )

    op.drop_table(
        "employees",
        schema="public",
    )
