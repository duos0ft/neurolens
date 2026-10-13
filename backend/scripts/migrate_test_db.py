import os

from alembic import command
from alembic.config import Config


def main() -> None:
    database_url = os.environ.get("TEST_MIGRATION_DATABASE_URL")

    if not database_url:
        raise RuntimeError("TEST_MIGRATION_DATABASE_URL must be configured")

    config = Config("alembic.ini")

    # Override the application migration URL for this process.
    os.environ["MIGRATION_DATABASE_URL"] = database_url

    command.upgrade(config, "head")


if __name__ == "__main__":
    main()
