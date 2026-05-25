"""Docker Sandbox for secure code execution.

Runs Python/Bash/JS code in isolated Docker containers with:
- No network access (--network none)
- Memory limits (--memory 512m)
- CPU limits (--cpus 1)
- Read-only filesystem except for mounted volumes
- Automatic cleanup on completion
"""
import os
import subprocess
import tempfile
import json
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class DockerSandbox:
    """Execute code inside a Docker container for security isolation."""

    def __init__(
        self,
        image: str = "python:3.11-slim",
        memory_limit: str = "512m",
        cpu_limit: str = "1.0",
        timeout: int = 30,
        network: bool = False,
    ):
        self.image = image
        self.memory_limit = memory_limit
        self.cpu_limit = cpu_limit
        self.timeout = timeout
        self.network = network

    def _ensure_image(self) -> bool:
        """Pull Docker image if not present."""
        try:
            result = subprocess.run(
                ["docker", "images", "-q", self.image],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if not result.stdout.strip():
                logger.info("Pulling Docker image %s...", self.image)
                subprocess.run(
                    ["docker", "pull", self.image],
                    capture_output=True,
                    timeout=120,
                    check=True,
                )
            return True
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
            return False

    def _is_docker_available(self) -> bool:
        """Check if Docker daemon is reachable."""
        try:
            subprocess.run(
                ["docker", "info"],
                capture_output=True,
                timeout=5,
                check=True,
            )
            return True
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
            return False

    def run_python(self, code: str) -> Dict[str, Any]:
        """Execute Python code in Docker container."""
        if not self._is_docker_available():
            return {"error": "Docker not available. Falling back to subprocess sandbox."}

        self._ensure_image()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            script_path = f.name

        try:
            # Create output directory for results
            with tempfile.TemporaryDirectory() as tmpdir:
                output_file = os.path.join(tmpdir, "output.json")

                # Wrapper script that captures stdout/stderr/returncode
                wrapper = f'''
import sys, json, traceback, os
from io import StringIO
old_stdout, old_stderr = sys.stdout, sys.stderr
sys.stdout = StringIO()
sys.stderr = StringIO()
try:
    exec(open("/code/script.py").read(), {{"__builtins__": __builtins__}})
    result = {{"stdout": sys.stdout.getvalue(), "stderr": sys.stderr.getvalue(), "success": True}}
except Exception as e:
    result = {{"stdout": sys.stdout.getvalue(), "stderr": sys.stderr.getvalue(), "error": str(e), "success": False}}
finally:
    sys.stdout, sys.stderr = old_stdout, old_stderr
    with open("/tmp/output.json", "w") as f:
        json.dump(result, f)
'''
                wrapper_path = os.path.join(tmpdir, "wrapper.py")
                with open(wrapper_path, "w") as f:
                    f.write(wrapper)

                # Copy user's script
                script_in_tmp = os.path.join(tmpdir, "script.py")
                with open(script_path, "r") as src, open(script_in_tmp, "w") as dst:
                    dst.write(src.read())

                cmd = [
                    "docker", "run", "--rm",
                    "--network", "none" if not self.network else "bridge",
                    "--memory", self.memory_limit,
                    "--cpus", self.cpu_limit,
                    "--read-only",
                    "-v", f"{tmpdir}:/code:ro",
                    "-v", f"{tmpdir}:/tmp:rw",
                    self.image,
                    "python", "/code/wrapper.py",
                ]

                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout + 5,
                )

                if os.path.exists(output_file):
                    with open(output_file, "r") as f:
                        return json.load(f)

                return {
                    "stdout": "",
                    "stderr": result.stderr,
                    "error": f"Docker execution failed (code {result.returncode}): {result.stderr[:500]}",
                    "success": False,
                }

        except subprocess.TimeoutExpired:
            return {"stdout": "", "stderr": "", "error": f"Docker execution timed out after {self.timeout}s", "success": False}
        except Exception as e:
            return {"stdout": "", "stderr": "", "error": str(e), "success": False}
        finally:
            if os.path.exists(script_path):
                os.unlink(script_path)

    def run_bash(self, code: str) -> Dict[str, Any]:
        """Execute bash code in Docker container."""
        if not self._is_docker_available():
            return {"error": "Docker not available"}

        try:
            cmd = [
                "docker", "run", "--rm",
                "--network", "none",
                "--memory", self.memory_limit,
                "--cpus", self.cpu_limit,
                "--read-only",
                self.image,
                "bash", "-c", code,
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout + 5,
            )

            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
                "success": result.returncode == 0,
            }
        except subprocess.TimeoutExpired:
            return {"stdout": "", "stderr": "", "error": f"Docker bash timed out after {self.timeout}s", "success": False}
        except Exception as e:
            return {"stdout": "", "stderr": "", "error": str(e), "success": False}


# Singleton instance
docker_sandbox = DockerSandbox()
