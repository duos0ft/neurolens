import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


EXPECTED_ACCESS = {
    "employees": (True, True, False, False, 3),
    "employee_profiles": (True, True, True, False, 3),
    "employee_invitations": (True, True, True, False, 3),
    "email_outbox": (True, True, True, False, 3),
    "auth_flows": (True, True, True, True, 4),
    "employee_sessions": (True, True, True, True, 4),
}


@pytest.mark.asyncio
async def test_database_runtime_permissions(
    test_admin_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with test_admin_session_factory() as session:
        result = await session.execute(
            text("""
                 SELECT
                     c.relname AS table_name,
                     c.relrowsecurity AS rls_enabled,
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
                     ) AS can_delete,
                     (
                         SELECT COUNT(*)
                         FROM pg_policies p
                         WHERE p.schemaname = 'public'
                           AND p.tablename = c.relname
                           AND 'neurolens_admin' = ANY(p.roles)
                     ) AS policy_count
                 FROM pg_class c
                          JOIN pg_namespace n ON n.oid = c.relnamespace
                 WHERE n.nspname = 'public'
                   AND c.relkind = 'r'
                   AND c.relname IN (
                                     'employees',
                                     'employee_profiles',
                                     'employee_invitations',
                                     'email_outbox',
                                     'auth_flows',
                                     'employee_sessions'
                     )
                 """)
        )

        rows = result.mappings().all()

    assert len(rows) == len(EXPECTED_ACCESS)

    for row in rows:
        table = row["table_name"]
        assert row["rls_enabled"] is True
        assert (
            row["can_select"],
            row["can_insert"],
            row["can_update"],
            row["can_delete"],
            row["policy_count"],
        ) == EXPECTED_ACCESS[table]


@pytest.mark.asyncio
async def test_employee_update_permissions(
    test_admin_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with test_admin_session_factory() as session:
        result = await session.execute(
            text("""
                 SELECT
                     column_name,
                     has_column_privilege(
                             'neurolens_admin',
                             'public.employees',
                             column_name,
                             'UPDATE'
                     ) AS can_update
                 FROM information_schema.columns
                 WHERE table_schema = 'public'
                   AND table_name = 'employees'
                 """)
        )

        permissions = dict(result.all())

    assert {column for column, allowed in permissions.items() if allowed} == {
        "auth0_user_id",
        "provisioning_status",
    }
