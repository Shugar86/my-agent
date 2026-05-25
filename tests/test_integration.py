"""Integration tests for skills, tools, auth, and session isolation."""

import sys
import os
import json
import tempfile
import shutil
import asyncio
import uuid
import gc
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.tool_registry import registry
from core.skill_loader import SkillLoader
from core.builder import AgentBuilder
from core.auth import create_access_token, decode_access_token, hash_password, verify_password
from core.memory_manager import MemoryManager
from core.event_bus import EventBus
from tools.vector_db import VectorDB

# ---------------------------------------------------------------------------
# Vector DB (ChromaDB) — RAG tools
# ---------------------------------------------------------------------------

def _cleanup_dir(path):
    """Force‑close any file handles and retry directory removal on Windows."""
    gc.collect()
    time.sleep(0.2)
    try:
        shutil.rmtree(path)
    except PermissionError:
        gc.collect()
        time.sleep(0.5)
        try:
            shutil.rmtree(path)
        except PermissionError:
            pass  # leave for temp cleanup


def test_vector_db_add_and_search():
    print("Testing VectorDB add and search...")
    tmpdir = tempfile.mkdtemp()
    persist_dir = os.path.join(tmpdir, "chroma")
    db = VectorDB(persist_dir=persist_dir)

    assert db.count() == 0

    doc_id = db.add_text("ИИ агенты — это программы, которые автономно выполняют задачи.",
                         source="manual")
    assert doc_id is not None
    assert db.count() == 1

    results = db.search("искусственный интеллект", n_results=5)
    assert len(results) >= 1
    assert "ИИ агенты" in results[0]["content"]

    docs = db.list_documents()
    assert len(docs) == 1
    assert docs[0]["source"] == "manual"

    db.close()
    _cleanup_dir(tmpdir)
    print("  PASSED: VectorDB add and search")


def test_vector_db_delete():
    print("Testing VectorDB delete...")
    tmpdir = tempfile.mkdtemp()
    db = VectorDB(persist_dir=os.path.join(tmpdir, "chroma"))

    id1 = db.add_text("Content A", source="src1")
    id2 = db.add_text("Content B", source="src2")
    assert db.count() == 2

    db.delete(id1)
    assert db.count() == 1
    docs = db.list_documents()
    assert docs[0]["id"] == id2

    db.close()
    _cleanup_dir(tmpdir)
    print("  PASSED: VectorDB delete")


def test_vector_db_empty_search():
    print("Testing VectorDB empty search...")
    tmpdir = tempfile.mkdtemp()
    db = VectorDB(persist_dir=os.path.join(tmpdir, "chroma"))
    results = db.search("anything")
    assert results == []
    db.close()
    _cleanup_dir(tmpdir)
    print("  PASSED: VectorDB empty search")


# ---------------------------------------------------------------------------
# Auth / JWT
# ---------------------------------------------------------------------------

def test_auth_jwt_with_user_id():
    print("Testing JWT with user_id...")
    token = create_access_token({"sub": "testuser", "user_id": "u_test123", "role": "user"})
    assert token is not None
    payload = decode_access_token(token)
    assert payload is not None
    assert payload["sub"] == "testuser"
    assert payload["user_id"] == "u_test123"
    assert payload["role"] == "user"
    print("  PASSED: JWT with user_id")


def test_auth_bad_token():
    print("Testing JWT with bad token...")
    result = decode_access_token("invalid.token.here")
    assert result is None
    print("  PASSED: JWT bad token")


def test_auth_password_hashing():
    print("Testing bcrypt hashing...")
    pwd = "my_secret_123"
    hashed = hash_password(pwd)
    assert hashed != pwd
    assert verify_password(pwd, hashed)
    assert not verify_password("wrong", hashed)
    print("  PASSED: bcrypt hashing")


# ---------------------------------------------------------------------------
# UserManager — multi-user operations
# ---------------------------------------------------------------------------

def test_user_manager_crud():
    print("Testing UserManager CRUD...")
    um = None
    try:
        async def run():
            from core.user_manager import UserManager
            nonlocal um
            um = UserManager()
            await um.connect()

            suffix = str(uuid.uuid4().hex[:6])
            alice = f"alice_{suffix}"

            u1 = await um.create_user(alice, "pass123")
            assert u1 is not None
            assert u1["username"] == alice
            assert u1["role"] == "user"

            dup = await um.create_user(alice, "other")
            assert dup is None  # duplicate blocked

            auth_ok = await um.authenticate(alice, "pass123")
            assert auth_ok is not None
            assert auth_ok["username"] == alice

            auth_bad = await um.authenticate(alice, "wrong")
            assert auth_bad is None

            auth_nonexist = await um.authenticate("bob_404", "x")
            assert auth_nonexist is None

            users = await um.list_users()
            assert len(users) >= 1

            keys = await um.get_api_keys(u1["id"])
            assert keys == {}

            await um.update_api_keys(u1["id"], {"openai": "sk-xxx"})
            keys2 = await um.get_api_keys(u1["id"])
            assert keys2["openai"] == "sk-xxx"

            await um.close()
        asyncio.run(run())
    finally:
        if um:
            try:
                asyncio.run(um.close())
            except Exception:
                pass
            if not _is_pg():
                try:
                    os.remove("data/users.db")
                except OSError:
                    pass
    print("  PASSED: UserManager CRUD")


# ---------------------------------------------------------------------------
# SkillLoader with Python module — full tool registration chain
# ---------------------------------------------------------------------------

def test_skill_loader_with_python_module():
    print("Testing SkillLoader with Python module...")
    tmpdir = tempfile.mkdtemp()
    skill_dir = os.path.join(tmpdir, "test_skill")
    os.makedirs(skill_dir)

    # SKILL.md
    with open(os.path.join(skill_dir, "SKILL.md"), "w", encoding="utf-8") as f:
        f.write("""---
name: test_skill
description: A skill with tool registration
tools:
  - my_tool
---

# Test Skill
""")

    # skill.py that registers a tool
    with open(os.path.join(skill_dir, "skill.py"), "w", encoding="utf-8") as f:
        f.write("""
from core.tool_registry import registry

def my_tool_func(param: str = "default") -> str:
    return f"processed: {param}"

def register_tools():
    registry.register(
        name="my_tool",
        description="A test tool from skill module",
        parameters={"type": "object", "properties": {"param": {"type": "string"}}},
        execute_fn=my_tool_func,
    )

def unregister_tools():
    registry.unregister("my_tool")
""")

    loader = SkillLoader(skills_dirs=[tmpdir])
    loader.load_all()

    assert "test_skill" in loader.skills
    assert loader.skills["test_skill"]["enabled"]

    # Tool should be registered in global registry via register_tools()
    assert registry.has("my_tool")

    # Execute the tool
    result = registry.execute("my_tool", param="hello")
    assert result == "processed: hello"

    # Get schemas
    schemas = loader.get_schemas(["my_tool"])
    assert len(schemas) == 1
    assert schemas[0]["function"]["name"] == "my_tool"

    # Cleanup: unregister
    loader.disable("test_skill")
    assert not registry.has("my_tool")

    shutil.rmtree(tmpdir)
    print("  PASSED: SkillLoader with Python module")


# ---------------------------------------------------------------------------
# Session isolation via user_id prefix
# ---------------------------------------------------------------------------

def _is_pg():
    return os.environ.get("DATABASE_URL") is not None


def test_session_user_id_prefix():
    print("Testing session isolation via user_id prefix...")
    tmpdir = tempfile.mkdtemp()
    db_path = os.path.join(tmpdir, "sessions.db")

    config = {"enabled": True, "scope": "task", "path": db_path}
    mm = MemoryManager(config)

    async def run():
        if _is_pg():
            await mm.connect_pg()

        alice_sid = "alice::session_1"
        bob_sid = "bob::session_1"

        if _is_pg():
            alice_session = await mm.get_session_async(alice_sid)
            alice_session.add_user_message("Hello from Alice")
            await mm.save_session_async(alice_session)

            bob_session = await mm.get_session_async(bob_sid)
            bob_session.add_user_message("Hello from Bob")
            await mm.save_session_async(bob_session)

            loaded_alice = await mm.get_session_async(alice_sid)
            loaded_bob = await mm.get_session_async(bob_sid)
        else:
            alice_session = mm.get_session(alice_sid)
            alice_session.add_user_message("Hello from Alice")
            mm.save_session(alice_session)

            bob_session = mm.get_session(bob_sid)
            bob_session.add_user_message("Hello from Bob")
            mm.save_session(bob_session)

            loaded_alice = mm.get_session(alice_sid)
            loaded_bob = mm.get_session(bob_sid)

        assert len(loaded_alice.messages) == 1
        assert loaded_alice.messages[0]["content"] == "Hello from Alice"

        assert len(loaded_bob.messages) == 1
        assert loaded_bob.messages[0]["content"] == "Hello from Bob"

        if _is_pg():
            results = await mm.search_async("Hello")
        else:
            results = mm.search("Hello")
        assert len(results) >= 2

        if _is_pg():
            await mm.close_pg()
        else:
            db = mm.get_db()
            if db:
                db.close()

    asyncio.run(run())
    shutil.rmtree(tmpdir)
    print("  PASSED: Session isolation via user_id prefix")


# ---------------------------------------------------------------------------
# Tool registry — schema format for LLM
# ---------------------------------------------------------------------------

def test_tool_registry_schema_format():
    print("Testing tool registry schema format...")
    from core.tool_registry import ToolRegistry

    reg = ToolRegistry()

    def fake_fn(x: int) -> int:
        return x * 2

    reg.register("calc_double", "Doubles a number",
                 {"type": "object", "properties": {"x": {"type": "integer"}}},
                 fake_fn)

    schemas = reg.get_schemas()
    assert len(schemas) == 1
    schema = schemas[0]
    assert schema["type"] == "function"
    assert schema["function"]["name"] == "calc_double"
    assert schema["function"]["description"] == "Doubles a number"
    assert schema["function"]["parameters"]["properties"]["x"]["type"] == "integer"

    # Execute via registry
    result = reg.execute("calc_double", x=5)
    assert result == 10

    # Invalid tool
    try:
        reg.execute("nonexistent")
        assert False, "Should have raised ValueError"
    except ValueError:
        pass

    print("  PASSED: Tool registry schema format")


# ---------------------------------------------------------------------------
# AgentBuilder builds an agent that can execute tools
# ---------------------------------------------------------------------------

def test_agent_build_and_tool_execution():
    print("Testing AgentBuilder build and tool execution...")
    from core.tool_registry import registry as global_reg

    # Register a tool temporarily
    def greet(person: str) -> str:
        return f"Hello, {person}!"

    global_reg.register("greet_tool", "Greets a person",
                        {"type": "object", "properties": {"person": {"type": "string"}}},
                        greet)

    builder = (AgentBuilder()
        .set_model({"primary": "test-model"})
        .set_role("Tester")
        .set_skills([])
        .set_tools(["greet_tool"])
        .set_memory({"enabled": False})
        .enable_events(False)
        .enable_compression(False)
        .enable_plugins(False))
    agent = builder.build()

    # Execute tool through agent's skills
    result = agent.skills.execute_tool("greet_tool", person="World")
    assert result == "Hello, World!"

    # Get LLM-ready schemas
    schemas = agent.skills.get_schemas(["greet_tool"])
    assert len(schemas) == 1
    assert schemas[0]["function"]["name"] == "greet_tool"

    global_reg.unregister("greet_tool")
    print("  PASSED: AgentBuilder tool execution")


# ---------------------------------------------------------------------------
# MemoryManager compress_session for SQLite (existing functionality)
# ---------------------------------------------------------------------------

def test_compress_session_sqlite():
    print("Testing compress_session with SQLite...")
    tmpdir = tempfile.mkdtemp()
    db_path = os.path.join(tmpdir, "compress.db")
    config = {"enabled": True, "scope": "task", "path": db_path}
    mm = MemoryManager(config)

    async def run():
        if _is_pg():
            await mm.connect_pg()

        if _is_pg():
            session = await mm.get_session_async("compress-test")
            session.add_user_message("First message")
            session.add_assistant_message("First response")
            session.add_user_message("Second message")
            session.add_assistant_message("Second response")
            await mm.save_session_async(session)
        else:
            session = mm.get_session("compress-test")
            session.add_user_message("First message")
            session.add_assistant_message("First response")
            session.add_user_message("Second message")
            session.add_assistant_message("Second response")
            mm.save_session(session)

        # Compress via PG directly (avoids nested event loop)
        if _is_pg():
            await mm._pg.compress_messages("compress-test", keep_head=1, keep_tail=1, summary_content="Summary here")
        else:
            mm.compress_session("compress-test", keep_head=1, keep_tail=1, summary_content="Summary here")

        if _is_pg():
            compressed = await mm.get_session_async("compress-test")
        else:
            compressed = mm.get_session("compress-test")
        # Original 4 messages → head(1) + summary(1) + tail(1) = 3
        assert len(compressed.messages) == 3
        assert compressed.messages[0]["content"] == "First message"
        if _is_pg():
            assert compressed.messages[1]["content"] == "[CONTEXT SUMMARY]: Summary here"
        else:
            assert compressed.messages[1]["content"] == "Summary here"
        assert compressed.messages[2]["content"] == "Second response"

        if _is_pg():
            await mm.close_pg()
        else:
            db = mm.get_db()
            if db:
                db.close()

    asyncio.run(run())
    shutil.rmtree(tmpdir)
    print("  PASSED: compress_session with SQLite")


# ---------------------------------------------------------------------------
# MCP tool naming convention
# ---------------------------------------------------------------------------

def test_mcp_tool_naming():
    print("Testing MCP tool naming convention...")
    from core.tool_registry import registry as global_reg

    def fake_mcp_tool(**kwargs) -> str:
            return "done"

    # MCP tools are named mcp_{server}_{tool}
    global_reg.register(
        name="mcp_filesystem_read",
        description="[MCP filesystem] Read a file",
        parameters={"type": "object", "properties": {"path": {"type": "string"}}},
        execute_fn=fake_mcp_tool,
    )

    assert global_reg.has("mcp_filesystem_read")
    tool = global_reg.get("mcp_filesystem_read")
    assert tool["name"] == "mcp_filesystem_read"
    assert "[MCP filesystem]" in tool["description"]

    result = global_reg.execute("mcp_filesystem_read", path="/test")
    assert result == "done"

    schemas = global_reg.get_schemas()
    mcp_schemas = [s for s in schemas if s["function"]["name"].startswith("mcp_")]
    assert len(mcp_schemas) >= 1

    global_reg.unregister("mcp_filesystem_read")
    print("  PASSED: MCP tool naming")


# ---------------------------------------------------------------------------
# Orchestrator — basic flow (no LLM)
# ---------------------------------------------------------------------------

def test_orchestrator_run_no_llm():
    print("Testing Orchestrator run flow (no LLM)...")
    import os
    from core.agent_store import AgentStore
    from core.orchestrator import Orchestrator

    # Use project registry to ensure agents are loaded
    registry_path = os.path.join(os.path.dirname(__file__), "..", "agents", "registry.json")
    store = AgentStore(registry_path=registry_path)
    orch = Orchestrator(store)

    agents_before = len(store.list_agents())
    assert agents_before >= 7  # Should have default agents

    # Non-streaming chat without reaching the LLM is hard to test,
    # but we can verify agent list works
    # We'll just ensure the store loads properly
    universal = store.get_agent("universal")
    assert universal is not None
    assert "rag" in universal.get("skills", [])

    print("  PASSED: Orchestrator basic")


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------

def test_all():
    print("=" * 60)
    print("Running integration tests...")
    print("=" * 60)

    tests = [
        test_vector_db_add_and_search,
        test_vector_db_delete,
        test_vector_db_empty_search,
        test_auth_jwt_with_user_id,
        test_auth_bad_token,
        test_auth_password_hashing,
        test_user_manager_crud,
        test_skill_loader_with_python_module,
        test_session_user_id_prefix,
        test_tool_registry_schema_format,
        test_agent_build_and_tool_execution,
        test_compress_session_sqlite,
        test_mcp_tool_naming,
        test_orchestrator_run_no_llm,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"  FAILED: {test.__name__}: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed, {passed + failed} total")
    print("=" * 60)
    return failed == 0


if __name__ == "__main__":
    success = test_all()
    sys.exit(0 if success else 1)
