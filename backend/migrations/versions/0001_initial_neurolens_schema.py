"""Initial NeuroLens database schema."""

import sqlalchemy as sa
from alembic import op

from migrations.runtime_access import RuntimeAccess, configure_runtime_access

revision = "0001_initial_neurolens"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "employees",
        sa.Column(
            "user_id",
            sa.UUID(),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("auth0_user_id", sa.Text(), unique=True),
        sa.Column("email", sa.Text()),
        sa.Column(
            "role",
            sa.Text(),
            nullable=False,
            server_default="employee",
        ),
        sa.Column(
            "status",
            sa.Text(),
            nullable=False,
            server_default="invited",
        ),
        sa.Column(
            "provisioning_status",
            sa.Text(),
            nullable=False,
            server_default="pending",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "role IN ('admin', 'employee')",
            name="employees_role_check",
        ),
        sa.CheckConstraint(
            "status IN ('invited', 'active', 'suspended')",
            name="employees_status_check",
        ),
        sa.CheckConstraint(
            "provisioning_status IN ('pending', 'completed', 'failed')",
            name="employees_provisioning_status_check",
        ),
        schema="public",
    )

    op.create_index(
        "employees_email_lower_idx",
        "employees",
        [sa.text("lower(email)")],
        unique=True,
        schema="public",
    )

    op.create_table(
        "employee_profiles",
        sa.Column(
            "user_id",
            sa.UUID(),
            sa.ForeignKey(
                "public.employees.user_id",
                ondelete="CASCADE",
            ),
            primary_key=True,
        ),
        sa.Column("display_name", sa.Text()),
        sa.Column("job_title", sa.Text()),
        sa.Column("department", sa.Text()),
        sa.Column("team", sa.Text()),
        sa.Column(
            "timezone",
            sa.Text(),
            nullable=False,
            server_default="UTC",
        ),
        sa.Column(
            "directness",
            sa.Text(),
            nullable=False,
            server_default="balanced",
        ),
        sa.Column(
            "response_length",
            sa.Text(),
            nullable=False,
            server_default="medium",
        ),
        sa.Column(
            "highlight_ambiguity",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
        sa.Column(
            "step_by_step_guidance",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
        sa.Column(
            "always_show_next_step",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
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

    op.create_table(
        "auth_flows",
        sa.Column(
            "id",
            sa.UUID(),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("state_hash", sa.Text(), nullable=False, unique=True),
        sa.Column("browser_nonce_hash", sa.Text(), nullable=False),
        sa.Column("oidc_nonce", sa.Text(), nullable=False),
        sa.Column("code_verifier", sa.Text(), nullable=False),
        sa.Column(
            "return_path",
            sa.Text(),
            nullable=False,
            server_default="/app",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "expires_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column("consumed_at", sa.DateTime(timezone=True)),
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

    op.create_table(
        "employee_sessions",
        sa.Column(
            "id",
            sa.UUID(),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("session_hash", sa.Text(), unique=True, nullable=False),
        sa.Column(
            "employee_id",
            sa.UUID(),
            sa.ForeignKey(
                "public.employees.user_id",
                ondelete="CASCADE",
            ),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "last_active_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "expires_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
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

    op.create_table(
        "employee_invitations",
        sa.Column(
            "id",
            sa.UUID(),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "employee_id",
            sa.UUID(),
            sa.ForeignKey(
                "public.employees.user_id",
                ondelete="CASCADE",
            ),
            nullable=False,
            unique=True,
        ),
        sa.Column("token_hash", sa.Text(), nullable=False, unique=True),
        sa.Column(
            "status",
            sa.Text(),
            nullable=False,
            server_default="pending",
        ),
        sa.Column(
            "attempt_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column("provisioning_started_at", sa.DateTime(timezone=True)),
        sa.Column("provisioning_attempt_id", sa.UUID()),
        sa.Column("auth0_creation_started_at", sa.DateTime(timezone=True)),
        sa.Column("last_error_code", sa.Text()),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("accepted_at", sa.DateTime(timezone=True)),
        sa.Column("cancelled_at", sa.DateTime(timezone=True)),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "status IN ("
            "'pending', 'provisioning', 'reconciliation_required', "
            "'ready', 'accepted', 'failed', 'expired', 'cancelled'"
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

    op.create_table(
        "email_outbox",
        sa.Column(
            "id",
            sa.UUID(),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "invitation_id",
            sa.UUID(),
            sa.ForeignKey(
                "public.employee_invitations.id",
                ondelete="CASCADE",
            ),
            nullable=False,
            unique=True,
        ),
        sa.Column(
            "status",
            sa.Text(),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("encrypted_token", sa.Text()),
        sa.Column(
            "attempt_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column("provider_message_id", sa.Text()),
        sa.Column("last_error_code", sa.Text()),
        sa.Column("delivery_attempt_id", sa.UUID()),
        sa.Column("delivery_started_at", sa.DateTime(timezone=True)),
        sa.Column("sent_at", sa.DateTime(timezone=True)),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'sending', 'sent', 'failed', 'reconciliation_required')",
            name="email_outbox_status_check",
        ),
        sa.CheckConstraint(
            "attempt_count >= 0",
            name="email_outbox_attempt_count_check",
        ),
        sa.CheckConstraint(
            "status NOT IN ('pending', 'sending') OR encrypted_token IS NOT NULL",
            name="email_outbox_pending_token_check",
        ),
        schema="public",
    )

    op.create_index(
        "email_outbox_status_idx",
        "email_outbox",
        ["status"],
        schema="public",
    )

    # Maintain updated_at consistently at the database layer.
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

    for table in (
        "employees",
        "employee_profiles",
        "employee_invitations",
    ):
        op.execute(
            f"""
            CREATE TRIGGER {table}_updated_at
            BEFORE UPDATE ON public.{table}
            FOR EACH ROW
            EXECUTE FUNCTION public.set_updated_at();
            """
        )

    # Provision the runtime role without embedding a password.
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_roles
                WHERE rolname = 'neurolens_admin'
            ) THEN
                CREATE ROLE neurolens_admin LOGIN NOBYPASSRLS;
            END IF;
        END;
        $$;
        """
    )

    op.execute("GRANT USAGE ON SCHEMA public TO neurolens_admin")

    # Permissions and RLS policies are managed centrally.
    # These policies authorize the trusted backend role, not individual employees.
    configure_runtime_access(
        "employees",
        RuntimeAccess.READ_WRITE,
        update_columns=("auth0_user_id", "provisioning_status"),
    )
    configure_runtime_access("employee_profiles", RuntimeAccess.READ_WRITE)
    configure_runtime_access("employee_invitations", RuntimeAccess.READ_WRITE)
    configure_runtime_access("email_outbox", RuntimeAccess.READ_WRITE)
    configure_runtime_access("auth_flows", RuntimeAccess.LIFECYCLE)
    configure_runtime_access("employee_sessions", RuntimeAccess.LIFECYCLE)


def downgrade() -> None:
    for table in (
        "employee_invitations",
        "employee_profiles",
        "employees",
    ):
        op.execute(f"DROP TRIGGER IF EXISTS {table}_updated_at ON public.{table}")

    op.execute("DROP FUNCTION IF EXISTS public.set_updated_at()")

    # Foreign-key dependencies require child tables first.
    for table in (
        "email_outbox",
        "employee_invitations",
        "employee_sessions",
        "auth_flows",
        "employee_profiles",
        "employees",
    ):
        op.drop_table(table, schema="public")
