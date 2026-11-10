import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from app.core.settings import settings
from app.models.application_settings import ApplicationSettings  # noqa: F401

# Import models so Alembic can discover their tables.
from app.models.auth_flow import AuthFlow  # noqa: F401
from app.models.base import Base
from app.models.contact_person import ContactPerson  # noqa: F401
from app.models.conversation import Conversation  # noqa: F401
from app.models.conversation_message import ConversationMessage  # noqa: F401
from app.models.email_outbox import EmailOutbox  # noqa: F401
from app.models.employee import Employee  # noqa: F401
from app.models.employee_invitation import EmployeeInvitation  # noqa: F401
from app.models.employee_profile import EmployeeProfile  # noqa: F401
from app.models.employee_session import EmployeeSession  # noqa: F401
from app.models.subtask import Subtask  # noqa: F401
from app.models.task import Task  # noqa: F401

config = context.config
migration_url = settings.migration_database_url or settings.database_url

MANAGED_TABLES = {
    "employees",
    "employee_profiles",
    "employee_sessions",
    "employee_invitations",
    "auth_flows",
    "email_outbox",
    "application_settings",
    "conversations",
    "conversation_messages",
    "contact_persons",
    "tasks",
    "subtasks",
}

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

config.set_main_option(
    "sqlalchemy.url",
    migration_url.replace("%", "%%"),
)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=migration_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_schemas=True,
        include_name=include_name,
        version_table_schema="public",
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def include_name(name, type_, parent_names):
    if type_ == "schema":
        return name in (None, "public")

    if type_ == "table":
        return parent_names.get("schema_name") in (None, "public") and name in MANAGED_TABLES

    return True


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        include_schemas=True,
        include_name=include_name,
        version_table_schema="public",
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
