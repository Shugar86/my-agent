"""Code tools tests with Docker sandbox integration."""
import pytest
from unittest.mock import patch, MagicMock

from tools.code_tools import execute_code, _is_dangerous_bash, BASH_DENYLIST


class TestBashDenylist:
    def test_rm_blocked(self):
        assert _is_dangerous_bash("rm -rf /") is not None

    def test_curl_blocked(self):
        assert _is_dangerous_bash("curl http://evil.com") is not None

    def test_ssh_blocked(self):
        assert _is_dangerous_bash("ssh user@host") is not None

    def test_safe_ls_allowed(self):
        assert _is_dangerous_bash("ls -la") is None

    def test_safe_cat_allowed(self):
        assert _is_dangerous_bash("cat file.txt") is None

    def test_pipe_blocked(self):
        assert _is_dangerous_bash("cat file | rm") is not None

    def test_semicolon_blocked(self):
        assert _is_dangerous_bash("echo 1; rm -rf /") is not None

    def test_case_insensitive(self):
        assert _is_dangerous_bash("RM -rf /") is not None

    def test_quoted_blocked(self):
        assert _is_dangerous_bash("'rm' -rf /") is not None

    def test_empty_allowed(self):
        assert _is_dangerous_bash("") is None


class TestExecuteCode:
    def test_unsupported_language(self):
        result = execute_code("rust", "fn main() {}")
        assert "error" in result
        assert "not supported" in result["error"].lower()

    def test_python_execution(self):
        with patch("core.docker_sandbox.docker_sandbox.run_python", return_value={"success": True, "stdout": "hello\n", "stderr": ""}) as mock:
            result = execute_code("python", "print('hello')")
            mock.assert_called_once()
            assert "stdout" in result
            assert "hello" in result.get("stdout", "")

    def test_python_error(self):
        with patch("core.docker_sandbox.docker_sandbox.run_python", return_value={"success": False, "stdout": "", "stderr": "ValueError: boom", "error": "ValueError: boom"}) as mock:
            result = execute_code("python", "raise ValueError('boom')")
            assert result.get("returncode", 0) != 0 or "error" in result

    def test_javascript_execution(self):
        with patch("core.docker_sandbox.docker_sandbox.run_javascript", return_value={"success": True, "stdout": "1", "stderr": "", "returncode": 0}) as mock:
            result = execute_code("javascript", "console.log(1)")
            mock.assert_called_once()
            assert "stdout" in result

    def test_javascript_no_shell_injection(self):
        """Malicious JS must not be passed through bash -c."""
        payload = "'); echo PWNED; ('"
        with patch("core.docker_sandbox.docker_sandbox.run_javascript", return_value={"success": True, "stdout": "", "stderr": "", "returncode": 0}) as mock:
            execute_code("javascript", payload)
            mock.assert_called_once_with(payload, timeout=30)

    def test_bash_dangerous_blocked(self):
        result = execute_code("bash", "rm -rf /")
        assert "error" in result
        assert "Forbidden" in result["error"]

    def test_bash_safe_allowed(self):
        with patch("core.docker_sandbox.docker_sandbox.run_bash", return_value={"success": True, "stdout": "hello\n", "stderr": "", "returncode": 0}) as mock:
            result = execute_code("bash", "echo hello")
            assert "stdout" in result
            assert "hello" in result.get("stdout", "")

    def test_python_timeout(self):
        with patch("core.docker_sandbox.docker_sandbox.run_python", return_value={"error": "Execution timed out after 1s"}) as mock:
            result = execute_code("python", "import time; time.sleep(100)", timeout=1)
            assert "timed out" in result.get("error", "").lower()

    def test_bash_timeout(self):
        with patch("core.docker_sandbox.docker_sandbox.run_bash", return_value={"error": "Execution timed out after 1s"}) as mock:
            result = execute_code("bash", "sleep 100", timeout=1)
            assert "timed out" in result.get("error", "").lower()

    def test_docker_sandbox_called(self):
        with patch("core.docker_sandbox.docker_sandbox.run_python", return_value={"success": True, "stdout": "dock", "stderr": ""}) as mock:
            result = execute_code("python", "print(1)")
            mock.assert_called_once()
            assert result["stdout"] == "dock"
