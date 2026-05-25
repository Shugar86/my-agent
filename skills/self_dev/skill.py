"""Self-Modification (Self-Dev) skill.

Allows the agent to read and modify its own source code.
CRITICAL: Disabled in production unless ENABLE_SELF_DEV=true.
All writes require human approval unless SELF_DEV_APPROVAL_REQUIRED is false.
"""
import os
import subprocess
from pathlib import Path

from core.tool_registry import registry
from core.validation import validate_safe_path

# Safety gates
_IS_PRODUCTION = os.environ.get("ENV", "").lower() == "production"
_SELF_DEV_ENABLED = os.environ.get("ENABLE_SELF_DEV", "false").lower() in ("true", "1", "yes")
SELF_DEV_APPROVAL_REQUIRED = os.environ.get("SELF_DEV_APPROVAL_REQUIRED", "true").lower() in ("true", "1", "yes")
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def _production_blocked() -> dict | None:
    """Return error payload when self-modification is disabled."""
    if _IS_PRODUCTION and not _SELF_DEV_ENABLED:
        return {
            "success": False,
            "error": "Self-modification is disabled in production. Set ENABLE_SELF_DEV=true to override.",
        }
    return None


def _is_inside_project(path: str) -> bool:
    try:
        target = _PROJECT_ROOT / path
        target.resolve().relative_to(_PROJECT_ROOT.resolve())
        return True
    except ValueError:
        return False


def read_source(file_path: str) -> dict:
    """Read a source file within the project."""
    blocked = _production_blocked()
    if blocked:
        return blocked
    if not validate_safe_path(file_path):
        return {"success": False, "error": "Invalid path"}
    if not _is_inside_project(file_path):
        return {"success": False, "error": "Path outside project directory"}
    full = _PROJECT_ROOT / file_path
    if not full.exists():
        return {"success": False, "error": "File not found"}
    try:
        content = full.read_text(encoding="utf-8")
        return {"success": True, "content": content, "path": str(full)}
    except Exception as e:
        return {"success": False, "error": str(e)}


def write_source(file_path: str, content: str, approved: bool = False) -> dict:
    """Write to a source file. Requires approval unless gate is disabled."""
    blocked = _production_blocked()
    if blocked:
        return blocked
    if not validate_safe_path(file_path):
        return {"success": False, "error": "Invalid path"}
    if not _is_inside_project(file_path):
        return {"success": False, "error": "Path outside project directory"}
    if SELF_DEV_APPROVAL_REQUIRED and not approved:
        return {
            "success": False,
            "error": "Human approval required. Set approved=True or disable SELF_DEV_APPROVAL_REQUIRED.",
            "requires_approval": True,
        }
    full = _PROJECT_ROOT / file_path
    try:
        full.parent.mkdir(parents=True, exist_ok=True)
        # Backup
        backup_path = None
        if full.exists():
            backup = full.with_suffix(full.suffix + ".backup")
            backup.write_bytes(full.read_bytes())
            backup_path = str(backup)
        full.write_text(content, encoding="utf-8")
        return {"success": True, "path": str(full), "backup": backup_path}
    except Exception as e:
        return {"success": False, "error": str(e)}


def run_tests() -> dict:
    """Run the project test suite."""
    blocked = _production_blocked()
    if blocked:
        return blocked
    try:
        result = subprocess.run(
            ["python", "-m", "pytest", "tests/", "-v", "--tb=short"],
            capture_output=True,
            text=True,
            timeout=300,
            cwd=str(_PROJECT_ROOT),
        )
        return {
            "success": result.returncode == 0,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def git_commit(message: str) -> dict:
    """Stage all changes and commit."""
    blocked = _production_blocked()
    if blocked:
        return blocked
    try:
        add = subprocess.run(
            ["git", "add", "-A"],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(_PROJECT_ROOT),
        )
        if add.returncode != 0:
            return {"success": False, "error": f"git add failed: {add.stderr}"}
        commit = subprocess.run(
            ["git", "commit", "-m", message],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(_PROJECT_ROOT),
        )
        if commit.returncode != 0:
            return {"success": False, "error": f"git commit failed: {commit.stderr}"}
        return {"success": True, "message": message, "output": commit.stdout}
    except Exception as e:
        return {"success": False, "error": str(e)}


def register_tools():
    if _IS_PRODUCTION and not _SELF_DEV_ENABLED:
        return
    registry.register(
        name="read_source",
        description="Read a source file inside the project directory.",
        parameters={
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "Relative path inside project"},
            },
            "required": ["file_path"],
        },
        execute_fn=read_source,
    )
    registry.register(
        name="write_source",
        description="Write to a source file inside the project. Requires approval by default.",
        parameters={
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "Relative path inside project"},
                "content": {"type": "string", "description": "New file content"},
                "approved": {"type": "boolean", "description": "Set to True to approve write"},
            },
            "required": ["file_path", "content"],
        },
        execute_fn=write_source,
    )
    registry.register(
        name="run_tests",
        description="Run the project pytest suite.",
        parameters={
            "type": "object",
            "properties": {},
            "required": [],
        },
        execute_fn=run_tests,
    )
    registry.register(
        name="git_commit",
        description="Stage and commit all changes with a message.",
        parameters={
            "type": "object",
            "properties": {
                "message": {"type": "string", "description": "Commit message"},
            },
            "required": ["message"],
        },
        execute_fn=git_commit,
    )


def unregister_tools():
    for name in ["read_source", "write_source", "run_tests", "git_commit"]:
        registry.unregister(name)
