import sys
import os
import tempfile
import shutil

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.skill_loader import SkillLoader
from core.builder import AgentBuilder


def test_skill_loader():
    print("Testing SkillLoader...")
    tmpdir = tempfile.mkdtemp()
    skill_dir = os.path.join(tmpdir, "test_skill")
    os.makedirs(skill_dir)

    with open(os.path.join(skill_dir, "SKILL.md"), "w", encoding="utf-8") as f:
        f.write("""---
name: test_skill
description: A test skill
version: 1.0
tools:
  - test_tool
---

# Test Skill
Instructions here
""")

    loader = SkillLoader(skills_dirs=[tmpdir])
    loader.load_all()

    assert "test_skill" in loader.skills
    assert loader.skills["test_skill"]["metadata"]["name"] == "test_skill"
    assert loader.skills["test_skill"]["metadata"]["description"] == "A test skill"
    assert loader.skills["test_skill"]["enabled"]

    context = loader.get_context()
    assert "test_skill" in context
    assert "A test skill" in context

    loader.disable("test_skill")
    assert not loader.skills["test_skill"]["enabled"]

    active = loader.get_active()
    assert "test_skill" not in active

    loader.enable("test_skill")
    assert loader.skills["test_skill"]["enabled"]

    shutil.rmtree(tmpdir)
    print("  PASSED: SkillLoader")


def test_skill_loader_empty_dir():
    print("Testing SkillLoader with empty dir...")
    loader = SkillLoader(skills_dirs=["/nonexistent/path"])
    loader.load_all()
    assert loader.skills == {}
    print("  PASSED: SkillLoader empty dir")


def test_skill_loader_no_skill_md():
    print("Testing SkillLoader without SKILL.md...")
    tmpdir = tempfile.mkdtemp()
    skill_dir = os.path.join(tmpdir, "no_md_skill")
    os.makedirs(skill_dir)

    loader = SkillLoader(skills_dirs=[tmpdir])
    loader.load_all()
    assert loader.skills == {}

    shutil.rmtree(tmpdir)
    print("  PASSED: SkillLoader no SKILL.md")


def test_builder():
    print("Testing AgentBuilder...")
    builder = (AgentBuilder()
        .set_model({"primary": "test-model"})
        .set_role("Test role")
        .set_skills([])
        .set_tools([])
        .set_memory({"enabled": False})
        .enable_events(False)
        .enable_compression(False)
        .enable_plugins(False)
    )

    agent = builder.build()
    assert agent.llm.primary == "test-model"
    assert agent.role == "Test role"
    assert agent.events is None
    assert agent.compressor is None
    assert agent.plugins is None
    print("  PASSED: AgentBuilder")


def test_builder_with_components():
    print("Testing AgentBuilder with all components...")
    builder = (AgentBuilder()
        .set_model({"primary": "test-model"})
        .set_role("Test role")
        .set_skills(["research"])
        .set_tools(["web_search"])
        .set_memory({"enabled": True, "scope": "task"})
        .enable_events(True)
        .enable_compression(True, max_tokens=2000)
        .enable_plugins(True)
    )

    agent = builder.build()
    assert agent.llm.primary == "test-model"
    assert agent.role == "Test role"
    assert agent.events is not None
    assert agent.compressor is not None
    assert agent.plugins is not None
    assert agent.memory.enabled
    print("  PASSED: AgentBuilder with components")


def test_builder_fluent():
    print("Testing AgentBuilder fluent interface...")
    builder = AgentBuilder()
    result = builder.set_model({}).set_role("").set_skills([])
    assert result is builder
    print("  PASSED: AgentBuilder fluent")


def test_all():
    print("=" * 60)
    print("Running skill/builder tests...")
    print("=" * 60)

    tests = [
        test_skill_loader,
        test_skill_loader_empty_dir,
        test_skill_loader_no_skill_md,
        test_builder,
        test_builder_with_components,
        test_builder_fluent,
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
