#!/usr/bin/env python3
"""One-time migration: SQLite data/agent.db → PostgreSQL DATABASE_URL."""

from __future__ import annotations

import argparse
import os
import sqlite3
import sys
from pathlib import Path

import psycopg2
from psycopg2.extras import execute_batch


TABLES = [
    "users",
    "teams",
    "team_members",
    "team_invites",
    "workflows",
    "workflow_runs",
    "workflow_templates",
    "usage_events",
    "integration_credentials",
    "onboarding_status",
    "scheduled_jobs_log",
]


def _sqlite_path() -> str:
    return os.getenv("SQLITE_PATH", "data/agent.db")


def _pg_url() -> str:
    url = os.getenv("DATABASE_URL", "")
    if not url.startswith("postgres"):
        print("Set DATABASE_URL=postgresql://...", file=sys.stderr)
        sys.exit(1)
    return url


def migrate(dry_run: bool = False) -> None:
    """Copy rows from SQLite into PostgreSQL for known tables."""
    sqlite_file = Path(_sqlite_path())
    if not sqlite_file.exists():
        print(f"No SQLite file at {sqlite_file} — nothing to migrate.")
        return

    src = sqlite3.connect(sqlite_file)
    src.row_factory = sqlite3.Row
    dst = psycopg2.connect(_pg_url())
    dst.autocommit = False

    try:
        for table in TABLES:
            try:
                rows = src.execute(f"SELECT * FROM {table}").fetchall()
            except sqlite3.OperationalError:
                continue
            if not rows:
                continue
            cols = rows[0].keys()
            col_list = ", ".join(cols)
            placeholders = ", ".join(["%s"] * len(cols))
            sql = f"INSERT INTO {table} ({col_list}) VALUES ({placeholders}) ON CONFLICT DO NOTHING"
            data = [tuple(row[c] for c in cols) for row in rows]
            print(f"{table}: {len(data)} rows")
            if not dry_run:
                with dst.cursor() as cur:
                    execute_batch(cur, sql, data, page_size=200)
        if dry_run:
            print("Dry run — no writes.")
        else:
            dst.commit()
            print("Migration complete.")
    except Exception:
        dst.rollback()
        raise
    finally:
        src.close()
        dst.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Migrate SQLite to PostgreSQL")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    migrate(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
