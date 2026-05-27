"""Code execution tools with Docker sandbox support ONLY.

Security: subprocess fallback removed. Docker sandbox is mandatory.
If Docker is unavailable, code execution returns an error.
"""
from core.tool_registry import registry
from core.docker_sandbox import docker_sandbox


BASH_DENYLIST = {
    "rm", "dd", "mkfs", "fdisk", "format", "del", "rd", "shutdown", "reboot",
    "poweroff", "halt", "init", "systemctl", "service", "kill", "pkill", "killall",
    "wget", "curl", "nc", "netcat", "ncat", "telnet", "ssh", "scp", "sftp",
    "python", "python3", "ruby", "perl", "node", "bash", "sh", ">", ">>", "|",
}


def _is_dangerous_bash(code: str) -> str | None:
    """Quick heuristic to catch obviously dangerous bash code."""
    lowered = code.lower()
    tokens = lowered.replace(";", " ").replace("|", " ").replace("&", " ").split()
    for token in tokens:
        clean = token.strip("'\"`")
        if clean in BASH_DENYLIST:
            return f"Forbidden command detected: '{clean}'. Use execute_code tool for Python/Node instead."
    return None


def execute_code(language, code, timeout=30):
    if language == "python":
        return _run_python(code, timeout)
    elif language == "javascript":
        return _run_javascript(code, timeout)
    elif language == "bash":
        return _run_bash(code, timeout)
    else:
        return {"error": f"Language '{language}' not supported. Use: python, javascript, bash"}


def _run_python(code, timeout):
    """Run Python code in Docker sandbox only."""
    docker_result = docker_sandbox.run_python(code, timeout=timeout)
    if docker_result.get("success"):
        return {
            "stdout": docker_result.get("stdout", ""),
            "stderr": docker_result.get("stderr", ""),
            "returncode": 0,
        }
    if "error" in docker_result:
        return {
            "stdout": docker_result.get("stdout", ""),
            "stderr": docker_result.get("stderr", ""),
            "error": docker_result["error"],
            "returncode": 1,
        }
    return {"error": "Docker sandbox unavailable. Code execution disabled."}


def _run_javascript(code, timeout):
    """Run JavaScript code in Docker sandbox (node image, file-based — no shell)."""
    docker_result = docker_sandbox.run_javascript(code, timeout=timeout)
    if docker_result.get("success"):
        return {
            "stdout": docker_result.get("stdout", ""),
            "stderr": docker_result.get("stderr", ""),
            "returncode": docker_result.get("returncode", 0),
        }
    if "error" in docker_result:
        return {
            "stdout": docker_result.get("stdout", ""),
            "stderr": docker_result.get("stderr", ""),
            "error": docker_result["error"],
            "returncode": 1,
        }
    return {"error": "Docker sandbox unavailable. Code execution disabled."}


def _run_bash(code, timeout):
    err = _is_dangerous_bash(code)
    if err:
        return {"error": err}

    docker_result = docker_sandbox.run_bash(code, timeout=timeout)
    if docker_result.get("success"):
        return {
            "stdout": docker_result.get("stdout", ""),
            "stderr": docker_result.get("stderr", ""),
            "returncode": docker_result.get("returncode", 0),
        }
    if "error" in docker_result:
        return {
            "stdout": docker_result.get("stdout", ""),
            "stderr": docker_result.get("stderr", ""),
            "error": docker_result["error"],
            "returncode": 1,
        }
    return {"error": "Docker sandbox unavailable. Code execution disabled."}


def register_tools():
    registry.register(
        name="execute_code",
        description="Execute code in a Docker sandbox (python, javascript, bash). Bash has command restrictions. Docker-only: no subprocess fallback.",
        parameters={
            "type": "object",
            "properties": {
                "language": {
                    "type": "string",
                    "enum": ["python", "javascript", "bash"],
                    "description": "Programming language",
                },
                "code": {"type": "string", "description": "Code to execute"},
                "timeout": {"type": "integer", "description": "Timeout in seconds (default 30)"},
            },
            "required": ["language", "code"],
        },
        execute_fn=execute_code,
    )


def unregister_tools():
    registry.unregister("execute_code")
