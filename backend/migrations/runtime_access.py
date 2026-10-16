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
    update_columns: tuple[str, ...] | None = None,
    schema: str = "public",
) -> None:
    identifiers = [table, schema, *(update_columns or ())]

    if not all(identifier.isidentifier() for identifier in identifiers):
        raise ValueError("Invalid database identifier")

    qualified_table = f'"{schema}"."{table}"'
    operations = PERMISSIONS[access]

    if update_columns is not None and "UPDATE" not in operations:
        raise ValueError("The selected access profile does not allow UPDATE")

    op.execute(f"REVOKE ALL ON TABLE {qualified_table} FROM PUBLIC")
    op.execute(f"ALTER TABLE {qualified_table} ENABLE ROW LEVEL SECURITY")

    for operation in operations:
        if operation == "UPDATE" and update_columns is not None:
            columns = ", ".join(f'"{column}"' for column in update_columns)

            op.execute(f"GRANT UPDATE ({columns}) ON TABLE {qualified_table} TO neurolens_admin")
        else:
            op.execute(f"GRANT {operation} ON TABLE {qualified_table} TO neurolens_admin")

        if operation == "INSERT":
            condition = "WITH CHECK (true)"
        elif operation == "UPDATE":
            condition = "USING (true) WITH CHECK (true)"
        else:
            condition = "USING (true)"

        policy_name = f"{table}_{operation.lower()}_runtime_policy"

        op.execute(
            f'CREATE POLICY "{policy_name}" '
            f"ON {qualified_table} "
            f"FOR {operation} "
            "TO neurolens_admin "
            f"{condition}"
        )
