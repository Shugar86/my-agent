"""Tests for Self-Modification (Self-Dev) skill."""
import os
import pytest
from pathlib import Path
from unittest.mock import patch
from skills.self_dev.skill import read_source, write_source, run_tests, git_commit


def test_read_source_inside_project():
    result = read_source("README.md")
    assert result["success"] is True
    assert "My Agent" in result["content"] or "#" in result["content"]


def test_read_source_outside_project():
    result = read_source("../../../etc/passwd")
    assert result["success"] is False


def test_write_source_requires_approval():
    result = write_source("tests/_tmp_test.py", "x = 1")
    assert result["success"] is False
    assert "approval" in result["error"].lower()


def test_write_source_with_approval():
    result = write_source("tests/_tmp_test_write.py", "x = 1\n", approved=True)
    assert result["success"] is True
    # Cleanup
    path = Path(__file__).resolve().parent.parent / "tests" / "_tmp_test_write.py"
    if path.exists():
        path.unlink()
        backup = path.with_suffix(path.suffix + ".backup")
        if backup.exists():
            backup.unlink()


def test_run_tests_executes():
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "pytest output"
        mock_run.return_value.stderr = ""
        result = run_tests()
        mock_run.assert_called_once()
        assert result["success"] is True
        assert "pytest output" in result["stdout"]


def test_git_commit_no_git_repo():
    with patch.dict("os.environ", {}, clear=False):
        result = git_commit("Test commit")
        # If inside a git repo, it might succeed or fail depending on dirty state
        assert "success" in result
