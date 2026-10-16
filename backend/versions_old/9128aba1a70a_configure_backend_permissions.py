"""configure_backend_permissions

Revision ID: 9128aba1a70a
Revises: 5e5a908468a1
Create Date: 2026-10-12 00:14:50.503204

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "9128aba1a70a"
down_revision: Union[str, Sequence[str], None] = "5e5a908468a1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_roles
                WHERE rolname = 'neurolens_admin'
            ) THEN
                CREATE ROLE neurolens_admin
                    LOGIN
                    NOBYPASSRLS;
            END IF;
        END
        $$;
        """
    )
    # Restrict access to application tables.
    op.execute("""
        REVOKE ALL ON TABLE
            public.employees,
            public.employee_profiles,
            public.auth_flows,
            public.employee_sessions
        FROM PUBLIC;
    """)

    # Allow backend role to access the public schema.
    op.execute("""
        GRANT USAGE ON SCHEMA public
        TO neurolens_admin;
    """)

    # Employee identity and profile access.
    op.execute("""
        GRANT SELECT ON
            public.employees,
            public.employee_profiles
        TO neurolens_admin;
    """)

    # Authentication flow and session management.
    op.execute("""
        GRANT SELECT, INSERT, UPDATE, DELETE ON
            public.auth_flows,
            public.employee_sessions
        TO neurolens_admin;
    """)

    # Employee records.
    op.execute("""
        CREATE POLICY "Backend reads employees"
        ON public.employees
        FOR SELECT
        TO neurolens_admin
        USING (true);
    """)

    # Employee communication preferences.
    op.execute("""
        CREATE POLICY "Backend reads employee profiles"
        ON public.employee_profiles
        FOR SELECT
        TO neurolens_admin
        USING (true);
    """)

    # Temporary OAuth authentication flows.
    op.execute("""
        CREATE POLICY "Backend manages OAuth flows"
        ON public.auth_flows
        FOR ALL
        TO neurolens_admin
        USING (true)
        WITH CHECK (true);
    """)

    # Persistent employee sessions.
    op.execute("""
        CREATE POLICY "Backend manages employee sessions"
        ON public.employee_sessions
        FOR ALL
        TO neurolens_admin
        USING (true)
        WITH CHECK (true);
    """)


def downgrade() -> None:
    op.execute("""
        DROP POLICY IF EXISTS "Backend manages employee sessions"
        ON public.employee_sessions;
    """)

    op.execute("""
        DROP POLICY IF EXISTS "Backend manages OAuth flows"
        ON public.auth_flows;
    """)

    op.execute("""
        DROP POLICY IF EXISTS "Backend reads employee profiles"
        ON public.employee_profiles;
    """)

    op.execute("""
        DROP POLICY IF EXISTS "Backend reads employees"
        ON public.employees;
    """)

    op.execute("""
        REVOKE ALL ON TABLE
            public.employees,
            public.employee_profiles,
            public.auth_flows,
            public.employee_sessions
        FROM neurolens_admin;
    """)
