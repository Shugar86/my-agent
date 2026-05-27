"""Unified database manager with SQLite/PostgreSQL dual mode.

Auto-detects database from DATABASE_URL environment variable.
SQLite: single-user, local dev
PostgreSQL: production with connection pooling
"""
import os
import sqlite3
import logging
from contextlib import contextmanager
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class DBManager:
    """Unified database interface supporting SQLite and PostgreSQL."""

    def __init__(self, database_url: Optional[str] = None):
        raw = database_url or os.getenv("DATABASE_URL") or "sqlite:///data/agent.db"
        self.database_url = raw.strip() or "sqlite:///data/agent.db"
        self._pool = None
        self._engine = None
        self._validate_production_config()
        self.db_type = "sqlite" if self.database_url.startswith("sqlite") else "postgres"
        self._init_db()

    def _validate_production_config(self) -> None:
        """Refuse SQLite in production — data layer must be PostgreSQL."""
        if os.getenv("ENV") != "production":
            return
        url = (self.database_url or "").strip()
        if not url or url.startswith("sqlite"):
            raise RuntimeError(
                "ENV=production requires PostgreSQL DATABASE_URL; "
                "SQLite fallback is disabled. Set DATABASE_URL=postgresql://..."
            )

    def _init_db(self):
        if self.db_type == "postgres":
            try:
                import asyncpg
                import psycopg2
                self._init_postgres()
            except ImportError as e:
                if os.getenv("ENV") == "production":
                    raise RuntimeError(
                        "PostgreSQL driver required in production"
                    ) from e
                logger.warning("PostgreSQL driver not available (%s), falling back to SQLite", e)
                self.database_url = "sqlite:///data/agent.db"
                self.db_type = "sqlite"
                self._init_sqlite()
        else:
            self._init_sqlite()

    def _init_sqlite(self):
        """Initialize SQLite with WAL mode and proper pragmas."""
        db_path = self.database_url.replace("sqlite:///", "")
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(db_path, check_same_thread=False)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.commit()
        conn.close()
        logger.info("SQLite initialized: %s (WAL mode)", db_path)

    def _init_postgres(self):
        """Initialize PostgreSQL connection pool."""
        try:
            import psycopg2.pool
            conninfo = self.database_url.replace("postgresql://", "").replace("postgres://", "")
            self._pool = psycopg2.pool.ThreadedConnectionPool(
                minconn=1,
                maxconn=20,
                dsn=self.database_url,
            )
            logger.info("PostgreSQL pool initialized: %s", self.database_url)
        except Exception as e:
            logger.error("Failed to init PostgreSQL pool: %s", e)
            raise

    @contextmanager
    def connection(self):
        """Get a database connection (context manager)."""
        if self.db_type == "sqlite":
            db_path = self.database_url.replace("sqlite:///", "")
            conn = sqlite3.connect(db_path, check_same_thread=False)
            conn.execute("PRAGMA foreign_keys=ON")
            conn.row_factory = sqlite3.Row
            try:
                yield conn
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                conn.close()
        else:
            if self._pool is None:
                raise RuntimeError("PostgreSQL pool not initialized")
            conn = self._pool.getconn()
            try:
                yield conn
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                self._pool.putconn(conn)

    def _adapt_sql(self, sql: str) -> str:
        """Translate SQLite-style placeholders for PostgreSQL."""
        if self.db_type == "postgres":
            return sql.replace("?", "%s")
        return sql

    @contextmanager
    def cursor(self):
        """Get a database cursor (context manager)."""
        with self.connection() as conn:
            if self.db_type == "postgres":
                import psycopg2.extras

                cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            else:
                cur = conn.cursor()
            try:
                yield cur
            finally:
                cur.close()

    def execute(self, sql: str, params=None):
        """Execute a SQL statement."""
        with self.cursor() as cur:
            cur.execute(self._adapt_sql(sql), params or ())
            return cur.rowcount

    def fetchone(self, sql: str, params=None):
        """Fetch one row."""
        with self.cursor() as cur:
            cur.execute(self._adapt_sql(sql), params or ())
            return cur.fetchone()

    def fetchall(self, sql: str, params=None):
        """Fetch all rows."""
        with self.cursor() as cur:
            cur.execute(self._adapt_sql(sql), params or ())
            return cur.fetchall()

    def table_exists(self, table_name: str) -> bool:
        """Check if a table exists."""
        if self.db_type == "sqlite":
            result = self.fetchone(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                (table_name,),
            )
        else:
            result = self.fetchone(
                "SELECT table_name FROM information_schema.tables WHERE table_name = %s",
                (table_name,),
            )
        return result is not None

    def create_tables(self):
        """Deprecated: schema is managed by Alembic migrations only."""
        import warnings
        warnings.warn(
            "create_tables() is deprecated; run alembic upgrade head instead",
            DeprecationWarning,
            stacklevel=2,
        )
        logger.info("create_tables() skipped — use Alembic migrations")

    def close(self):
        """Close all connections."""
        if self._pool:
            self._pool.closeall()
            logger.info("PostgreSQL pool closed")


# Singleton instance
db = DBManager()
