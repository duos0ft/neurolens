from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "67180e3f7e88"
down_revision: Union[str, Sequence[str], None] = "75f18722a832"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "email_outbox",
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "invitation_id",
            sa.UUID(),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Text(),
            server_default=sa.text("'pending'"),
            nullable=False,
        ),
        sa.Column(
            "encrypted_token",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "attempt_count",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column(
            "provider_message_id",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "last_error_code",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "sent_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'sending', 'sent', 'failed')",
            name="email_outbox_status_check",
        ),
        sa.CheckConstraint(
            "status NOT IN ('pending', 'sending') OR encrypted_token IS NOT NULL",
            name="email_outbox_pending_token_check",
        ),
        sa.CheckConstraint(
            "attempt_count >= 0",
            name="email_outbox_attempt_count_check",
        ),
        sa.ForeignKeyConstraint(
            ["invitation_id"],
            ["public.employee_invitations.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("invitation_id"),
        schema="public",
    )

    op.create_index(
        "email_outbox_status_idx",
        "email_outbox",
        ["status"],
        unique=False,
        schema="public",
    )

    op.execute("GRANT SELECT, INSERT, UPDATE ON TABLE public.email_outbox TO neurolens_admin")

    op.execute("ALTER TABLE public.email_outbox ENABLE ROW LEVEL SECURITY")

    op.execute(
        """
        CREATE POLICY email_outbox_runtime_policy
        ON public.email_outbox
        FOR ALL
        TO neurolens_admin
        USING (true)
        WITH CHECK (true)
        """
    )


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS email_outbox_runtime_policy ON public.email_outbox")

    op.drop_index(
        "email_outbox_status_idx",
        table_name="email_outbox",
        schema="public",
    )

    op.drop_table(
        "email_outbox",
        schema="public",
    )
