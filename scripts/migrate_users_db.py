#!/usr/bin/env python3
"""Migrate users from legacy data/users.db into agent.db users table.

Idempotent: skips usernames already present in agent.db.
Run after `alembic upgrade head`.
"""

from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path


def migrate(users_db: Path, agent_db: Path) -> int:
    """Copy users from users.db into agent.db. Returns count migrated."""
    if not users_db.exists():
        print(f"No legacy users.db at {users_db}")
        return 0
    if not agent_db.exists():
        print(f"Target agent.db not found: {agent_db}")
        return 0

    src = sqlite3.connect(str(users_db))
    src.row_factory = sqlite3.Row
    dst = sqlite3.connect(str(agent_db))

    count = 0
    for row in src.execute("SELECT * FROM users"):
        username = row["username"]
        if dst.execute(
            "SELECT 1 FROM users WHERE username=?", (username,)
        ).fetchone():
            continue

        pwd = row["password_hash"] if "password_hash" in row.keys() else row["password"]
        dst.execute(
            """INSERT INTO users
               (id, username, password_hash, email, role, api_keys, auth_provider)
               VALUES (?,?,?,?,?,?,?)""",
            (
                row["id"],
                username,
                pwd,
                row["email"] if "email" in row.keys() else None,
                row["role"],
                row["api_keys"] if "api_keys" in row.keys() else "{}",
                row["auth_provider"] if "auth_provider" in row.keys() else "local",
            ),
        )
        count += 1

    dst.commit()
    src.close()
    dst.close()
    print(f"Migrated {count} users from {users_db} -> {agent_db}")
    return count


def main() -> None:
    parser = argparse.ArgumentParser(description="Migrate users.db to agent.db")
    parser.add_argument("--users-db", default="data/users.db")
    parser.add_argument("--agent-db", default="data/agent.db")
    args = parser.parse_args()
    migrate(Path(args.users_db), Path(args.agent_db))


if __name__ == "__main__":
    main()
