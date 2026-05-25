import sys
import os
import json
import tempfile
import shutil
import asyncio

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.config import load_config, save_config, _merge, resolve_env_vars
from core.tool_registry import ToolRegistry, registry
from core.event_bus import EventBus
from core.memory_manager import MemoryManager, Session
from core.context_compressor import ContextCompressor
from core.plugin_manager import PluginManager


def test_tool_registry():
    print("Testing ToolRegistry...")
    reg = ToolRegistry()

    reg.register("test_tool", "A test tool", {"type": "object"}, lambda x: x * 2)
    assert reg.has("test_tool")
    assert reg.get("test_tool")["name"] == "test_tool"

    schemas = reg.get_schemas()
    assert len(schemas) == 1
    assert schemas[0]["function"]["name"] == "test_tool"

    result = reg.execute("test_tool", x=5)
    assert result == 10

    reg.unregister("test_tool")
    assert not reg.has("test_tool")

    print("  PASSED: ToolRegistry")


def test_tool_registry_global():
    print("Testing global registry...")
    registry.register("global_test", "Test", {"type": "object"}, lambda: "ok")
    assert registry.has("global_test")
    assert registry.execute("global_test") == "ok"
    registry.unregister("global_test")
    print("  PASSED: global registry")


def test_event_bus():
    print("Testing EventBus...")
    bus = EventBus()

    results = []

    def handler1(value):
        results.append(value * 2)

    def handler2(value):
        results.append(value + 10)

    bus.on("test_event", handler1)
    bus.on("test_event", handler2)

    bus.emit("test_event", value=5)
    assert 10 in results
    assert 15 in results

    bus.off("test_event", handler1)
    results.clear()
    bus.emit("test_event", value=5)
    assert 15 in results
    assert 10 not in results

    once_results = []

    def once_handler(x):
        once_results.append(x)

    bus.once("once_event", once_handler)
    bus.emit("once_event", x=42)
    assert once_results == [42]
    bus.emit("once_event", x=99)
    assert once_results == [42]

    events = bus.list_events()
    assert "test_event" in events

    print("  PASSED: EventBus")


def _is_pg():
    return os.environ.get("DATABASE_URL") is not None


def test_memory_manager():
    print("Testing MemoryManager...")
    tmpdir = tempfile.mkdtemp()
    db_path = os.path.join(tmpdir, "test.db")

    config = {"enabled": True, "scope": "task", "path": db_path}
    mm = MemoryManager(config)

    async def run():
        if _is_pg():
            await mm.connect_pg()

        if _is_pg():
            session = await mm.get_session_async("test-1")
        else:
            session = mm.get_session("test-1")
        assert session.id == "test-1"
        assert session.messages == []

        session.add_user_message("Hello")
        session.add_assistant_message("Hi there!")
        session.add_tool_result("tc-1", "result")

        assert len(session.messages) == 3
        assert session.messages[0]["role"] == "user"
        assert session.messages[1]["role"] == "assistant"
        assert session.messages[2]["role"] == "tool"

        if _is_pg():
            await mm.save_session_async(session)
            loaded = await mm.get_session_async("test-1")
        else:
            mm.save_session(session)
            loaded = mm.get_session("test-1")
        assert len(loaded.messages) == 3
        assert loaded.messages[0]["content"] == "Hello"

        if _is_pg():
            results = await mm.search_async("Hello")
        else:
            results = mm.search("Hello")
        assert len(results) > 0

        if _is_pg():
            await mm.close_pg()
        else:
            db = mm.get_db()
            if db:
                db.close()

    asyncio.run(run())
    shutil.rmtree(tmpdir)
    print("  PASSED: MemoryManager")


def test_memory_disabled():
    print("Testing MemoryManager disabled...")
    config = {"enabled": False}
    mm = MemoryManager(config)
    session = mm.get_session("test")
    assert session.id == "test"
    mm.save_session(session)
    print("  PASSED: MemoryManager disabled")


def test_session():
    print("Testing Session...")
    s = Session("s1")
    s.add_user_message("test")
    s.add_assistant_message("response")
    assert len(s.messages) == 2
    assert s.messages[0]["role"] == "user"
    assert s.messages[1]["role"] == "assistant"
    print("  PASSED: Session")


def test_config_merge():
    print("Testing config merge...")
    default = {"a": 1, "b": {"c": 2, "d": 3}}
    override = {"b": {"c": 10}, "e": 5}
    result = _merge(default, override)
    assert result["a"] == 1
    assert result["b"]["c"] == 10
    assert result["b"]["d"] == 3
    assert result["e"] == 5
    print("  PASSED: config merge")


def test_config_save_load():
    print("Testing config save/load...")
    tmpdir = tempfile.mkdtemp()
    path = os.path.join(tmpdir, "test.yaml")

    config = {"name": "test", "model": {"primary": "test-model"}, "skills": ["a", "b"]}
    save_config(config, path)

    loaded = load_config(path)
    assert loaded["name"] == "test"
    assert loaded["model"]["primary"] == "test-model"
    assert loaded["skills"] == ["a", "b"]

    shutil.rmtree(tmpdir)
    print("  PASSED: config save/load")


def test_config_env_vars():
    print("Testing config env vars...")
    os.environ["TEST_API_KEY"] = "secret123"
    config = {"api_key": "${TEST_API_KEY}", "other": "value"}
    resolved = resolve_env_vars(config)
    assert resolved["api_key"] == "secret123"
    assert resolved["other"] == "value"
    del os.environ["TEST_API_KEY"]
    print("  PASSED: config env vars")


def test_context_compressor():
    print("Testing ContextCompressor...")
    from core.llm_gateway import LLMGateway

    llm = LLMGateway({})
    compressor = ContextCompressor(llm, max_tokens=100, threshold_ratio=0.5)

    messages = [{"role": "system", "content": "You are a bot"}]
    for i in range(20):
        messages.append({"role": "user", "content": f"Message {i}" * 10})
        messages.append({"role": "assistant", "content": f"Response {i}" * 10})

    assert compressor.needs_compression(messages)

    compressed = compressor.compress(messages, keep_last=2)
    assert len(compressed) < len(messages)
    assert compressed[0]["role"] == "system"

    short_messages = [{"role": "user", "content": "Hi"}]
    assert not compressor.needs_compression(short_messages)

    print("  PASSED: ContextCompressor")


def test_plugin_manager():
    print("Testing PluginManager...")
    tmpdir = tempfile.mkdtemp()
    plugin_path = os.path.join(tmpdir, "test_plugin.py")

    with open(plugin_path, "w") as f:
        f.write("""
class Plugin:
    name = "test_plugin"
    def __init__(self):
        pass
    def on_message(self, **kwargs):
        return "handled"
    def unload(self):
        pass
""")

    pm = PluginManager(plugins_dirs=[tmpdir])
    pm.discover()
    assert "test_plugin" in pm.plugins

    results = pm.emit("on_message", message="test")
    assert len(results) > 0

    pm.unload("test_plugin")
    assert "test_plugin" not in pm.plugins

    shutil.rmtree(tmpdir)
    print("  PASSED: PluginManager")


def test_plugin_manager_no_dir():
    print("Testing PluginManager with non-existent dir...")
    pm = PluginManager(plugins_dirs=["/nonexistent/path"])
    pm.discover()
    assert pm.plugins == {}
    print("  PASSED: PluginManager no dir")


def test_all():
    print("=" * 60)
    print("Running all tests...")
    print("=" * 60)

    tests = [
        test_tool_registry,
        test_tool_registry_global,
        test_event_bus,
        test_memory_manager,
        test_memory_disabled,
        test_session,
        test_config_merge,
        test_config_save_load,
        test_config_env_vars,
        test_context_compressor,
        test_plugin_manager,
        test_plugin_manager_no_dir,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"  FAILED: {test.__name__}: {e}")
            failed += 1

    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed, {passed + failed} total")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = test_all()
    sys.exit(0 if success else 1)
