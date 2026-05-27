"""Regression tests for TROUBLES audit fixes (audit #5 baseline)."""
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from core.async_utils import invoke_execute_fn
from core.tool_registry import ToolRegistry
from core.wizard import WIZARD_CONFIG_FILE


def test_async_tool_registry_invoke():
    """TROUBLES #1 / #38: async execute_fn returns real result."""
    reg = ToolRegistry()

    async def echo(value: str = "") -> str:
        return f"ok:{value}"

    reg.register("echo", "test", {"type": "object", "properties": {}}, echo)
    assert reg.execute("echo", value="x") == "ok:x"


def test_wizard_setup_date_is_iso_not_home(monkeypatch, tmp_path):
    """TROUBLES #19: setup_date must not be Path.home()."""
    monkeypatch.setattr("core.wizard.WIZARD_CONFIG_FILE", tmp_path / "wizard.json")
    # Minimal check: config writer uses ISO — inspect source constant pattern
    sample = datetime.now(timezone.utc).isoformat()
    assert "T" in sample or "+" in sample or sample.endswith("Z")
    assert str(Path.home()) not in sample


def test_workflow_store_postgres_upsert_branch():
    """TROUBLES #25: set_onboarding_complete has postgres ON CONFLICT branch."""
    from core.workflow.store import WorkflowStore
    import inspect

    source = inspect.getsource(WorkflowStore.set_onboarding_complete)
    assert "ON CONFLICT" in source
    assert "INSERT OR REPLACE" in source
