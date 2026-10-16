from enum import StrEnum

from alembic import op


class RuntimeAccess(StrEnum):
    READ_ONLY = "read_only"
    READ_WRITE = "read_write"
    LIFECYCLE = "lifecycle"


PERMISSIONS: dict[RuntimeAccess, tuple[str, ...]] = {
    RuntimeAccess.READ_ONLY: ("SELECT",),
    RuntimeAccess.READ_WRITE: ("SELECT", "INSERT", "UPDATE"),
    RuntimeAccess.LIFECYCLE: ("SELECT", "INSERT", "UPDATE", "DELETE"),
}


def configure_runtime_access(
    table: str,
    access: RuntimeAccess = RuntimeAccess.READ_WRITE,
    *,
    schema: str = "public",
) -> None:
    if not table.isidentifier() or not schema.isidentifier():
        raise ValueError("Invalid database identifier")

    qualified_table = f'"{schema}"."{table}"'
    privileges = PERMISSIONS[access]

    op.execute(f"GRANT {', '.join(privileges)} ON TABLE {qualified_table} TO neurolens_admin")

    op.execute(f"ALTER TABLE {qualified_table} ENABLE ROW LEVEL SECURITY")

    for operation in privileges:
        policy_name = f"{table}_{operation.lower()}_runtime_policy"

        if operation == "INSERT":
            condition = "WITH CHECK (true)"
        elif operation == "SELECT" or operation == "DELETE":
            condition = "USING (true)"
        else:
            condition = "USING (true) WITH CHECK (true)"

        op.execute(
            f'CREATE POLICY "{policy_name}" '
            f"ON {qualified_table} "
            f"FOR {operation} "
            f"TO neurolens_admin "
            f"{condition}"
        )


def remove_runtime_access(
    table: str,
    *,
    schema: str = "public",
) -> None:
    if not table.isidentifier() or not schema.isidentifier():
        raise ValueError("Invalid database identifier")

    qualified_table = f'"{schema}"."{table}"'

    for operation in ("SELECT", "INSERT", "UPDATE", "DELETE"):
        policy_name = f"{table}_{operation.lower()}_runtime_policy"

        op.execute(f'DROP POLICY IF EXISTS "{policy_name}" ON {qualified_table}')

    op.execute(
        f"REVOKE SELECT, INSERT, UPDATE, DELETE ON TABLE {qualified_table} FROM neurolens_admin"
    )
