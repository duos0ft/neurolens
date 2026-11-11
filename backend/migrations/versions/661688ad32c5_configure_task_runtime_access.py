"""configure task runtime access

Revision ID: 661688ad32c5
Revises: af438d0ccb0c
Create Date: 2026-11-08 20:57:18.293093

"""

from typing import Sequence, Union

from alembic import op

from migrations.runtime_access import RuntimeAccess, configure_runtime_access

# revision identifiers, used by Alembic.
revision: str = "661688ad32c5"
down_revision: Union[str, Sequence[str], None] = "af438d0ccb0c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TRIGGER tasks_updated_at
            BEFORE UPDATE ON public.tasks
            FOR EACH ROW
            EXECUTE FUNCTION public.set_updated_at()
        """
    )

    op.execute(
        """
        CREATE TRIGGER subtasks_updated_at
            BEFORE UPDATE ON public.subtasks
            FOR EACH ROW
            EXECUTE FUNCTION public.set_updated_at()
        """
    )

    configure_runtime_access(
        "tasks",
        RuntimeAccess.LIFECYCLE,
    )

    configure_runtime_access(
        "subtasks",
        RuntimeAccess.LIFECYCLE,
    )


def downgrade() -> None:
    for table in ("subtasks", "tasks"):
        for operation in ("SELECT", "INSERT", "UPDATE", "DELETE"):
            policy_name = f"{table}_{operation.lower()}_runtime_policy"

            op.execute(f'DROP POLICY IF EXISTS "{policy_name}" ON public."{table}"')

        op.execute(
            f'REVOKE SELECT, INSERT, UPDATE, DELETE ON TABLE public."{table}" FROM neurolens_admin'
        )

        op.execute(f'ALTER TABLE public."{table}" DISABLE ROW LEVEL SECURITY')

    op.execute(
        """
        DROP TRIGGER IF EXISTS subtasks_updated_at
        ON public.subtasks
        """
    )

    op.execute(
        """
        DROP TRIGGER IF EXISTS tasks_updated_at
        ON public.tasks
        """
    )
