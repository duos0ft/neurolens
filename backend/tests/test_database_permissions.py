import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.base import Base

# Expected SQL privileges for the trusted backend database role.
# New tables must declare an explicit access profile here.
EXPECTED_ACCESS = {
    "employees": ("SELECT", "INSERT"),
    "employee_profiles": ("SELECT", "INSERT", "UPDATE"),
    "employee_invitations": ("SELECT", "INSERT", "UPDATE"),
    "email_outbox": ("SELECT", "INSERT", "UPDATE"),
    "auth_flows": ("SELECT", "INSERT", "UPDATE", "DELETE"),
    "employee_sessions": ("SELECT", "INSERT", "UPDATE", "DELETE"),
    "application_settings": ("SELECT", "INSERT"),
    "contact_persons": ("SELECT", "INSERT"),
    "conversations": ("SELECT", "INSERT", "UPDATE", "DELETE"),
    "conversation_messages": ("SELECT", "INSERT", "UPDATE", "DELETE"),
}


# Tables with intentionally restricted column-level UPDATE permissions.
EXPECTED_UPDATE_COLUMNS = {
    "employees": {
        "auth0_user_id",
        "provisioning_status",
        "status",
    },
    "application_settings": {
        "organization_name",
        "enable_task_assistance",
        "enable_policy_assistance",
        "enable_sentiment_analysis",
    },
    "contact_persons": {
        "name",
        "job_title",
        "email",
        "department",
        "responsibility",
        "is_primary",
        "is_active",
    },
}


# Column-level UPDATE permissions still require UPDATE RLS policies,
# even when full-table UPDATE permission is intentionally denied.
EXPECTED_POLICY_OPERATIONS = {
    table: set(operations) | ({"UPDATE"} if table in EXPECTED_UPDATE_COLUMNS else set())
    for table, operations in EXPECTED_ACCESS.items()
}


@pytest.mark.asyncio
async def test_all_application_tables_have_rls(
    test_admin_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    expected_tables = {
        table.name for table in Base.metadata.tables.values() if table.schema == "public"
    }

    # Every SQLAlchemy table must have a declared access profile.
    assert expected_tables == set(EXPECTED_ACCESS)

    async with test_admin_session_factory() as session:
        result = await session.execute(
            text(
                """
                SELECT
                    c.relname AS table_name,
                    c.relrowsecurity AS rls_enabled
                FROM pg_class c
                         JOIN pg_namespace n
                              ON n.oid = c.relnamespace
                WHERE n.nspname = 'public'
                  AND c.relkind IN ('r', 'p')
                  AND c.relname != 'alembic_version'
                """
            )
        )

        database_tables = {row.table_name: row.rls_enabled for row in result}

    assert set(database_tables) == expected_tables

    for table_name, enabled in database_tables.items():
        assert enabled, f"RLS is disabled on {table_name}"


@pytest.mark.asyncio
async def test_database_runtime_permissions(
    test_admin_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with test_admin_session_factory() as session:
        result = await session.execute(
            text(
                """
                SELECT
                    c.relname AS table_name,
                    has_table_privilege(
                            'neurolens_admin', c.oid, 'SELECT'
                    ) AS can_select,
                    has_table_privilege(
                            'neurolens_admin', c.oid, 'INSERT'
                    ) AS can_insert,
                    has_table_privilege(
                            'neurolens_admin', c.oid, 'UPDATE'
                    ) AS can_update,
                    has_table_privilege(
                            'neurolens_admin', c.oid, 'DELETE'
                    ) AS can_delete
                FROM pg_class c
                         JOIN pg_namespace n
                              ON n.oid = c.relnamespace
                WHERE n.nspname = 'public'
                  AND c.relkind IN ('r', 'p')
                  AND c.relname != 'alembic_version'
                """
            )
        )

        rows = result.mappings().all()

    assert {row["table_name"] for row in rows} == set(EXPECTED_ACCESS)

    for row in rows:
        table_name = row["table_name"]
        expected = EXPECTED_ACCESS[table_name]

        actual = {
            operation
            for operation, column in (
                ("SELECT", "can_select"),
                ("INSERT", "can_insert"),
                ("UPDATE", "can_update"),
                ("DELETE", "can_delete"),
            )
            if row[column]
        }

        assert actual == set(expected), (
            f"Incorrect privileges on {table_name}: expected {set(expected)}, got {actual}"
        )


@pytest.mark.asyncio
async def test_runtime_policy_definitions(
    test_admin_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with test_admin_session_factory() as session:
        result = await session.execute(
            text(
                """
                SELECT
                    tablename,
                    policyname,
                    cmd,
                    permissive,
                    roles,
                    qual,
                    with_check
                FROM pg_policies
                WHERE schemaname = 'public'
                """
            )
        )

        rows = result.mappings().all()

    actual_policies: dict[str, dict[str, dict]] = {
        table: {} for table in EXPECTED_POLICY_OPERATIONS
    }

    for row in rows:
        table_name = row["tablename"]

        assert table_name in EXPECTED_POLICY_OPERATIONS, f"Unexpected RLS policy on {table_name}"

        operation = row["cmd"]

        assert operation not in actual_policies[table_name], (
            f"Duplicate RLS policy for {table_name}: {operation}"
        )

        expected_name = f"{table_name}_{operation.lower()}_runtime_policy"

        assert row["policyname"] == expected_name
        assert row["permissive"] == "PERMISSIVE"
        assert row["roles"] == ["neurolens_admin"]

        if operation == "INSERT":
            assert row["qual"] is None
            assert row["with_check"] == "true"

        elif operation == "UPDATE":
            assert row["qual"] == "true"
            assert row["with_check"] == "true"

        else:
            assert row["qual"] == "true"
            assert row["with_check"] is None

        actual_policies[table_name][operation] = dict(row)

    for table_name, expected in EXPECTED_POLICY_OPERATIONS.items():
        actual = set(actual_policies[table_name])

        assert actual == expected, (
            f"Incorrect RLS policies on {table_name}: expected {expected}, got {actual}"
        )


@pytest.mark.asyncio
async def test_column_update_permissions(
    test_admin_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with test_admin_session_factory() as session:
        for table_name, expected_columns in EXPECTED_UPDATE_COLUMNS.items():
            result = await session.execute(
                text(
                    """
                    SELECT
                        column_name,
                        has_column_privilege(
                                'neurolens_admin',
                                :table_name,
                                column_name,
                                'UPDATE'
                        ) AS can_update
                    FROM information_schema.columns
                    WHERE table_schema = 'public'
                      AND table_name = :table
                    """
                ),
                {
                    "table_name": f"public.{table_name}",
                    "table": table_name,
                },
            )

            permissions = dict(result.all())

            assert permissions, f"No columns found for {table_name}"

            allowed_columns = {column for column, allowed in permissions.items() if allowed}

            assert allowed_columns == expected_columns, (
                f"Incorrect UPDATE columns on {table_name}: "
                f"expected {expected_columns}, got {allowed_columns}"
            )
