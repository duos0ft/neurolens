import os
from pathlib import Path

from alembic import command
from alembic.config import Config
from dotenv import load_dotenv
from sqlalchemy.engine import make_url


def main() -> None:
    backend_dir = Path(__file__).resolve().parents[1]

    load_dotenv(
        dotenv_path=backend_dir / ".env",
        override=False,
    )

    database_url = os.environ.get("BASELINE_TEST_DATABASE_URL")

    if not database_url:
        raise RuntimeError("BASELINE_TEST_DATABASE_URL must be configured")

    url = make_url(database_url)

    if (
        url.database != "neurolens"
        or url.host not in ("localhost", "127.0.0.1")
        or url.get_backend_name() != "postgresql"
    ):
        raise RuntimeError(
            "Baseline migrations must target the local neurolens PostgreSQL database"
        )

    config = Config(str(backend_dir / "alembic.ini"))

    config.set_main_option(
        "script_location",
        str(backend_dir / "migrations"),
    )

    config.set_main_option(
        "version_locations",
        str(backend_dir / "migrations" / "baseline"),
    )

    # The existing migrations/env.py reads Settings, so setting
    # an environment variable alone may not be enough if the
    # Settings object was already initialized.
    os.environ["MIGRATION_DATABASE_URL"] = database_url

    command.upgrade(config, "head")


if __name__ == "__main__":
    main()
