import os

from core.tool_registry import registry
from core.validation import validate_safe_path_or_error


def _resolve_path(path: str) -> str:
    """Resolve relative paths against AGENT_WORKSPACE (or cwd)."""
    if os.path.isabs(path):
        return path
    workspace = os.environ.get("AGENT_WORKSPACE") or os.getcwd()
    return os.path.join(workspace, path)


def file_read(path):
    resolved = _resolve_path(path)
    err = validate_safe_path_or_error(resolved, "file")
    if err:
        return {"error": err}
    try:
        with open(resolved, "r", encoding="utf-8") as f:
            return f.read()
    except OSError as e:
        return {"error": str(e)}


def file_write(path, content):
    resolved = _resolve_path(path)
    err = validate_safe_path_or_error(resolved, "file")
    if err:
        return {"error": err}
    try:
        parent = os.path.dirname(resolved)
        if parent:
            os.makedirs(parent, exist_ok=True)
        with open(resolved, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Written {len(content)} chars to {resolved}"
    except OSError as e:
        return {"error": str(e)}


def register_tools():
    registry.register(
        name="file_read",
        description="Read content from a file",
        parameters={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path"},
            },
            "required": ["path"],
        },
        execute_fn=file_read,
    )

    registry.register(
        name="file_write",
        description="Write content to a file",
        parameters={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path"},
                "content": {"type": "string", "description": "Content to write"},
            },
            "required": ["path", "content"],
        },
        execute_fn=file_write,
    )


def unregister_tools():
    registry.unregister("file_read")
    registry.unregister("file_write")
