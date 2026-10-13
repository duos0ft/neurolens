"""add email outbox reconciliation state

Revision ID: ca4e8dd4caab
Revises: 400d6732fec8
Create Date: 2026-10-13 23:32:32.944383

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "ca4e8dd4caab"
down_revision: Union[str, Sequence[str], None] = "400d6732fec8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint(
        "email_outbox_status_check",
        "email_outbox",
        type_="check",
        schema="public",
    )

    op.create_check_constraint(
        "email_outbox_status_check",
        "email_outbox",
        "status IN ('pending', 'sending', 'sent', 'failed', 'reconciliation_required')",
        schema="public",
    )


def downgrade() -> None:
    op.drop_constraint(
        "email_outbox_status_check",
        "email_outbox",
        type_="check",
        schema="public",
    )

    op.create_check_constraint(
        "email_outbox_status_check",
        "email_outbox",
        "status IN ('pending', 'sending', 'sent', 'failed')",
        schema="public",
    )
