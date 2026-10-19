"""create application settings

Revision ID: c80ac5306ab5
Revises: 26d35e61bdd4
Create Date: 2026-10-20 00:33:31.627448

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from migrations.runtime_access import RuntimeAccess, configure_runtime_access

# revision identifiers, used by Alembic.
revision: str = "c80ac5306ab5"
down_revision: Union[str, Sequence[str], None] = "26d35e61bdd4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "application_settings",
        sa.Column(
            "id",
            sa.Integer(),
            primary_key=True,
        ),
        sa.Column(
            "organization_name",
            sa.Text(),
            nullable=False,
            server_default="NeuroLens",
        ),
        sa.Column(
            "enable_task_assistance",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
        sa.Column(
            "enable_policy_assistance",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
        sa.Column(
            "enable_sentiment_analysis",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
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
            "id = 1",
            name="application_settings_singleton_check",
        ),
        sa.CheckConstraint(
            "length(btrim(organization_name)) > 0",
            name="application_settings_organization_name_check",
        ),
        schema="public",
    )

    op.execute(
        """
        CREATE TRIGGER application_settings_updated_at
            BEFORE UPDATE ON public.application_settings
            FOR EACH ROW
            EXECUTE FUNCTION public.set_updated_at()
        """
    )

    configure_runtime_access(
        "application_settings",
        RuntimeAccess.READ_WRITE,
        update_columns=(
            "organization_name",
            "enable_task_assistance",
            "enable_policy_assistance",
            "enable_sentiment_analysis",
        ),
    )

    op.execute(
        """
        INSERT INTO public.application_settings (
            id,
            organization_name,
            enable_task_assistance,
            enable_policy_assistance,
            enable_sentiment_analysis
        )
        VALUES (
                   1,
                   'NeuroLens',
                   true,
                   true,
                   false
               )
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP TRIGGER IF EXISTS application_settings_updated_at
        ON public.application_settings
        """
    )

    op.drop_table(
        "application_settings",
        schema="public",
    )
