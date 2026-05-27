"""Tools package — register standalone tool modules on first import."""

from __future__ import annotations

import importlib
import logging
import pkgutil
from pathlib import Path

logger = logging.getLogger(__name__)

_tools_registered = False


def register_all_tools() -> int:
    """Import each ``tools/*.py`` module and call ``register_tools()`` if present.

    Returns:
        Number of modules that exposed ``register_tools`` and were loaded.
    """
    global _tools_registered
    package_dir = Path(__file__).resolve().parent
    registered = 0
    for info in pkgutil.iter_modules([str(package_dir)]):
        if info.name.startswith("_"):
            continue
        try:
            module = importlib.import_module(f"tools.{info.name}")
            if hasattr(module, "register_tools"):
                module.register_tools()
                registered += 1
        except Exception as exc:
            logger.warning("Failed to register tools from tools.%s: %s", info.name, exc)
    _tools_registered = True
    return registered


def ensure_tools_registered() -> None:
    """Register tools once (idempotent)."""
    if not _tools_registered:
        register_all_tools()


ensure_tools_registered()
