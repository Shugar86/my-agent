"""Google Sign-in user provisioning tests."""

from __future__ import annotations

import asyncio
import os
import pytest

os.environ["ENV"] = "test"


@pytest.fixture
def user_manager(tmp_path):
    import sqlite3
    from core.user_manager import UserManager

    db_file = tmp_path / "users.db"
    um = UserManager()
    um._use_pg = False
    um._sqlite_conn = sqlite3.connect(str(db_file), check_same_thread=False)
    um._sqlite_conn.row_factory = sqlite3.Row
    um._init_sqlite()
    return um


@pytest.mark.asyncio
async def test_get_or_create_from_google(user_manager):
    user = await user_manager.get_or_create_from_google("test@example.com", name="Test")
    assert user is not None
    assert user["auth_provider"] == "google"
    again = await user_manager.get_or_create_from_google("test@example.com")
    assert again["id"] == user["id"]


@pytest.mark.asyncio
async def test_local_email_blocks_google(user_manager):
    await user_manager.create_user("localuser", "Password123!", role="user")
    user = await user_manager.get_user_by_username("localuser")
    user_manager._sqlite_conn.execute(
        "UPDATE users SET email = ? WHERE id = ?", ("local@example.com", user["id"])
    )
    user_manager._sqlite_conn.commit()
    result = await user_manager.get_or_create_from_google("local@example.com")
    assert result is None
