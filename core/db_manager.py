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
        self.database_url = database_url or os.getenv("DATABASE_URL", "sqlite:///data/agent.db")
        self._pool = None
        self._engine = None
        self.db_type = "sqlite" if self.database_url.startswith("sqlite") else "postgres"
        self._init_db()

    def _init_db(self):
        if self.db_type == "postgres":
            try:
                import asyncpg
                import psycopg2
                self._init_postgres()
            except ImportError as e:
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
        """Create all application tables."""
        sessions_sql = """
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            agent_id TEXT NOT NULL,
            user_id TEXT,
            messages TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        users_sql = """
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            email TEXT,
            role TEXT DEFAULT 'user',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        skills_sql = """
        CREATE TABLE IF NOT EXISTS installed_skills (
            name TEXT PRIMARY KEY,
            version TEXT,
            source TEXT,
            installed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        metrics_sql = """
        CREATE TABLE IF NOT EXISTS metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            value REAL NOT NULL,
            labels TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """

        if self.db_type == "postgres":
            # Adjust SQLite-specific AUTOINCREMENT for PostgreSQL
            metrics_sql = metrics_sql.replace(
                "id INTEGER PRIMARY KEY AUTOINCREMENT",
                "id SERIAL PRIMARY KEY"
            )
            sessions_sql = sessions_sql.replace("TEXT", "VARCHAR")
            users_sql = users_sql.replace("TEXT", "VARCHAR")
            skills_sql = skills_sql.replace("TEXT", "VARCHAR")

        for sql in [sessions_sql, users_sql, skills_sql, metrics_sql]:
            self.execute(sql)

        logger.info("Database tables created/verified")

    def close(self):
        """Close all connections."""
        if self._pool:
            self._pool.closeall()
            logger.info("PostgreSQL pool closed")


# Singleton instance
db = DBManager()
