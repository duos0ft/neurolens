"""create contact persons

Revision ID: b690ce05e392
Revises: 08731a735d3f
Create Date: 2026-10-24 19:40:41.735140

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from migrations.runtime_access import RuntimeAccess, configure_runtime_access

# revision identifiers, used by Alembic.
revision: str = "b690ce05e392"
down_revision: Union[str, Sequence[str], None] = "08731a735d3f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "contact_persons",
        sa.Column(
            "id",
            sa.UUID(),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "name",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "job_title",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "email",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "department",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "responsibility",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "is_primary",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        sa.Column(
            "is_active",
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
            "length(btrim(name)) > 0",
            name="contact_persons_name_check",
        ),
        sa.CheckConstraint(
            "length(btrim(email)) > 0",
            name="contact_persons_email_check",
        ),
        sa.CheckConstraint(
            "length(btrim(responsibility)) > 0",
            name="contact_persons_responsibility_check",
        ),
        sa.UniqueConstraint(
            "email",
            name="contact_persons_email_unique",
        ),
        schema="public",
    )

    op.create_index(
        "ix_contact_persons_active_responsibility",
        "contact_persons",
        ["responsibility"],
        unique=False,
        schema="public",
        postgresql_where=sa.text("is_active = true"),
    )

    op.create_index(
        "uq_contact_persons_primary_responsibility",
        "contact_persons",
        ["responsibility"],
        unique=True,
        schema="public",
        postgresql_where=sa.text("is_primary = true AND is_active = true"),
    )

    op.execute(
        """
        CREATE TRIGGER contact_persons_updated_at
            BEFORE UPDATE ON public.contact_persons
            FOR EACH ROW
            EXECUTE FUNCTION public.set_updated_at()
        """
    )

    configure_runtime_access(
        "contact_persons",
        RuntimeAccess.READ_WRITE,
        update_columns=(
            "name",
            "job_title",
            "email",
            "department",
            "responsibility",
            "is_primary",
            "is_active",
        ),
    )


def downgrade() -> None:
    op.execute(
        """
        DROP TRIGGER IF EXISTS contact_persons_updated_at
        ON public.contact_persons
        """
    )

    op.drop_index(
        "uq_contact_persons_primary_responsibility",
        table_name="contact_persons",
        schema="public",
    )

    op.drop_index(
        "ix_contact_persons_active_responsibility",
        table_name="contact_persons",
        schema="public",
    )

    op.drop_table(
        "contact_persons",
        schema="public",
    )
