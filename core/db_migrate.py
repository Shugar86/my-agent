"""Run Alembic migrations on application startup."""

import logging
import os
from pathlib import Path

from alembic import command
from alembic.config import Config

logger = logging.getLogger(__name__)


def run_migrations(database_url: str | None = None) -> None:
    """Apply pending Alembic migrations to agent.db.

    Args:
        database_url: Optional SQLAlchemy URL override (defaults to DATABASE_URL env).
    """
    project_root = Path(__file__).resolve().parent.parent
    alembic_ini = project_root / "alembic.ini"
    if not alembic_ini.exists():
        logger.warning("alembic.ini not found, skipping migrations")
        return

    url = database_url or os.environ.get("DATABASE_URL", "sqlite:///data/agent.db")
    data_dir = project_root / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    cfg = Config(str(alembic_ini))
    cfg.set_main_option("sqlalchemy.url", url)
    cfg.set_main_option("script_location", str(project_root / "alembic"))

    try:
        from sqlalchemy import create_engine, inspect
        engine = create_engine(url)
        inspector = inspect(engine)
        existing = inspector.get_table_names()
        if "users" in existing and "alembic_version" not in existing:
            command.stamp(cfg, "001_init")
            logger.info("Stamped existing database at revision 001_init")
        command.upgrade(cfg, "head")
        logger.info("Alembic migrations applied (head)")
    except Exception as exc:
        logger.exception("Alembic migration failed: %s", exc)
        raise
