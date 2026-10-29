
import pytest

from app.tools.workspace import AgentWorkspace
from app.tools.python_verifier import verify_python_syntax


def test_workspace_writes_and_reads_files():
    with AgentWorkspace() as workspace:
        workspace.write_file(
            "src/example.py",
            "def add(a, b): return a + b",
        )

        assert workspace.read_file("src/example.py") == (
            "def add(a, b): return a + b"
        )


def test_workspace_rejects_path_traversal():
    with AgentWorkspace() as workspace:
        with pytest.raises(ValueError):
            workspace.write_file(
                "../outside.py",
                "print('unsafe')",
            )


def test_workspace_rejects_absolute_paths():
    with AgentWorkspace() as workspace:
        with pytest.raises(ValueError):
            workspace.write_file(
                "/tmp/outside.py",
                "print('unsafe')",
            )


def test_valid_python_syntax():
    result = verify_python_syntax(
        "def add(a, b):\n    return a + b"
    )

    assert result.passed is True


def test_invalid_python_syntax():
    result = verify_python_syntax(
        "def add(a, b)\n    return a + b"
    )

    assert result.passed is False
