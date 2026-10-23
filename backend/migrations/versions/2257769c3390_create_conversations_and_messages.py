"""create conversations and messages

Revision ID: 2257769c3390
Revises: c80ac5306ab5
Create Date: 2026-10-23 21:51:23.762208

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from migrations.runtime_access import configure_runtime_access, RuntimeAccess

# revision identifiers, used by Alembic.
revision: str = "2257769c3390"
down_revision: Union[str, Sequence[str], None] = "c80ac5306ab5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "conversations",
        sa.Column(
            "id",
            sa.UUID(),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "employee_id",
            sa.UUID(),
            sa.ForeignKey(
                "public.employees.user_id",
                ondelete="CASCADE",
            ),
            nullable=False,
        ),
        sa.Column("title", sa.Text()),
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
        schema="public",
    )

    op.create_index(
        "ix_public_conversations_employee_id",
        "conversations",
        ["employee_id"],
        schema="public",
    )

    op.create_table(
        "conversation_messages",
        sa.Column(
            "id",
            sa.UUID(),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "conversation_id",
            sa.UUID(),
            sa.ForeignKey(
                "public.conversations.id",
                ondelete="CASCADE",
            ),
            nullable=False,
        ),
        sa.Column("role", sa.Text(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("model", sa.Text()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "role IN ('user', 'assistant')",
            name="conversation_messages_role_check",
        ),
        schema="public",
    )

    op.create_index(
        "ix_public_conversation_messages_conversation_id",
        "conversation_messages",
        ["conversation_id"],
        schema="public",
    )

    op.execute(
        """
        CREATE TRIGGER conversations_updated_at
            BEFORE UPDATE ON public.conversations
            FOR EACH ROW
            EXECUTE FUNCTION public.set_updated_at()
        """
    )

    configure_runtime_access(
        "conversations",
        RuntimeAccess.LIFECYCLE,
    )

    configure_runtime_access(
        "conversation_messages",
        RuntimeAccess.LIFECYCLE,
    )


def downgrade() -> None:
    op.execute(
        """
        DROP TRIGGER IF EXISTS conversations_updated_at
        ON public.conversations
        """
    )

    op.drop_table(
        "conversation_messages",
        schema="public",
    )

    op.drop_table(
        "conversations",
        schema="public",
    )

