import os
from core.tool_registry import registry


def file_read(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return {"error": str(e)}


def file_write(path, content):
    try:
        os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Written {len(content)} chars to {path}"
    except Exception as e:
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
