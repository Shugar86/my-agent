"""Tests for file_tools path sandbox."""
import os

import pytest

from tools.file_tools import file_read, file_write


@pytest.fixture
def workspace(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_WORKSPACE", str(tmp_path))
    monkeypatch.chdir(tmp_path)
    return tmp_path


def test_file_read_within_workspace(workspace):
    target = workspace / "hello.txt"
    target.write_text("hi", encoding="utf-8")
    assert file_read("hello.txt") == "hi"


def test_file_read_blocks_traversal(workspace):
    result = file_read("../../etc/passwd")
    assert isinstance(result, dict)
    assert "error" in result


def test_file_write_blocks_traversal(workspace):
    result = file_write("../outside.txt", "nope")
    assert isinstance(result, dict)
    assert "error" in result
