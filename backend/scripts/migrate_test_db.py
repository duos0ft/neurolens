import os
from pathlib import Path

from alembic import command
from alembic.config import Config
from dotenv import load_dotenv


def main() -> None:
    backend_dir = Path(__file__).resolve().parents[1]

    load_dotenv(
        dotenv_path=backend_dir / ".env",
        override=False,
    )

    database_url = os.environ.get("TEST_MIGRATION_DATABASE_URL")

    if not database_url:
        raise RuntimeError("TEST_MIGRATION_DATABASE_URL must be configured")

    config = Config(str(backend_dir / "alembic.ini"))

    os.environ["MIGRATION_DATABASE_URL"] = database_url

    command.upgrade(config, "head")


if __name__ == "__main__":
    main()
