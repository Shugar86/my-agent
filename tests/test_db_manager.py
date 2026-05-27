"""DB Manager tests for SQLite/PostgreSQL dual mode."""
import os
import pytest
import tempfile
from unittest.mock import patch, MagicMock

from core.db_manager import DBManager, db
from core.db_migrate import run_migrations


class TestDBManagerSQLite:
    @pytest.fixture
    def sqlite_db(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            path = f.name
        run_migrations(f"sqlite:///{path}")
        manager = DBManager(f"sqlite:///{path}")
        yield manager
        manager.close()
        os.unlink(path)

    def test_init_sqlite(self, sqlite_db):
        assert sqlite_db.db_type == "sqlite"
        assert sqlite_db.table_exists("sessions")
        assert sqlite_db.table_exists("users")
        assert sqlite_db.table_exists("installed_skills")
        assert sqlite_db.table_exists("metrics")

    def test_execute_insert_and_fetch(self, sqlite_db):
        sqlite_db.execute("INSERT INTO users (id, username, password_hash) VALUES (?, ?, ?)", ("u1", "alice", "hash"))
        row = sqlite_db.fetchone("SELECT * FROM users WHERE id = ?", ("u1",))
        assert row is not None
        assert dict(row)["username"] == "alice"

    def test_fetchall(self, sqlite_db):
        sqlite_db.execute("INSERT INTO users (id, username, password_hash) VALUES (?, ?, ?)", ("u1", "alice", "h1"))
        sqlite_db.execute("INSERT INTO users (id, username, password_hash) VALUES (?, ?, ?)", ("u2", "bob", "h2"))
        rows = sqlite_db.fetchall("SELECT * FROM users ORDER BY id")
        assert len(rows) == 2
        assert dict(rows[0])["username"] == "alice"
        assert dict(rows[1])["username"] == "bob"

    def test_transaction_rollback_on_error(self, sqlite_db):
        try:
            with sqlite_db.connection() as conn:
                conn.execute("INSERT INTO users (id, username, password_hash) VALUES (?, ?, ?)", ("u3", "charlie", "h3"))
                raise ValueError("forced error")
        except ValueError:
            pass
        row = sqlite_db.fetchone("SELECT * FROM users WHERE id = ?", ("u3",))
        assert row is None

    def test_table_exists_negative(self, sqlite_db):
        assert not sqlite_db.table_exists("nonexistent_table")

    def test_context_cursor(self, sqlite_db):
        with sqlite_db.cursor() as cur:
            cur.execute("SELECT 1")
            assert cur.fetchone()[0] == 1

    def test_metrics_table(self, sqlite_db):
        sqlite_db.execute("INSERT INTO metrics (name, value) VALUES (?, ?)", ("latency", 42.0))
        rows = sqlite_db.fetchall("SELECT * FROM metrics WHERE name = ?", ("latency",))
        assert len(rows) == 1
        assert dict(rows[0])["value"] == 42.0

    def test_sessions_table(self, sqlite_db):
        sqlite_db.execute(
            "INSERT INTO sessions (id, agent_id, messages) VALUES (?, ?, ?)",
            ("s1", "universal", "[]"),
        )
        row = sqlite_db.fetchone("SELECT * FROM sessions WHERE id = ?", ("s1",))
        assert dict(row)["agent_id"] == "universal"

    def test_installed_skills_table(self, sqlite_db):
        sqlite_db.execute(
            "INSERT INTO installed_skills (name, version, source) VALUES (?, ?, ?)",
            ("sql_db", "1.0", "builtin"),
        )
        row = sqlite_db.fetchone("SELECT * FROM installed_skills WHERE name = ?", ("sql_db",))
        assert dict(row)["version"] == "1.0"


class TestDBManagerPostgreSQL:
    def test_init_postgres_when_url_provided(self):
        with patch("psycopg2.pool.ThreadedConnectionPool") as mock_pool:
            mock_pool.return_value = MagicMock()
            manager = DBManager("postgresql://user:pass@localhost/db")
            assert manager.db_type == "postgres"
            mock_pool.assert_called_once()

    def test_fallback_to_sqlite_when_postgres_driver_missing(self):
        import builtins

        real_import = builtins.__import__

        def _import(name, globals=None, locals=None, fromlist=(), level=0):
            if name in ("psycopg2", "asyncpg") or (fromlist and fromlist[0] in ("psycopg2", "asyncpg")):
                raise ImportError(f"{name} not available")
            return real_import(name, globals, locals, fromlist, level)

        with patch("builtins.__import__", side_effect=_import):
            manager = DBManager("postgresql://localhost/db")
            assert manager.db_type == "sqlite"

    def test_postgres_table_exists(self):
        with patch("psycopg2.pool.ThreadedConnectionPool") as mock_pool:
            mock_conn = MagicMock()
            mock_cur = MagicMock()
            mock_cur.fetchone.return_value = ("users",)
            mock_conn.cursor.return_value = mock_cur
            mock_pool.return_value.getconn.return_value = mock_conn
            manager = DBManager("postgresql://localhost/db")
            manager._pool = mock_pool.return_value
            assert manager.table_exists("users")


class TestDBManagerSingleton:
    def test_default_singleton(self):
        assert db.db_type == "sqlite"
