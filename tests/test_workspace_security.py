
import pytest

from app.tools.sandbox.workspace_security import (
    WorkspaceSecurityError,
    validate_execution_file,
)
from app.tools.workspace import AgentWorkspace


def test_valid_workspace_file():
    with AgentWorkspace() as workspace:
        workspace.write_file("hello.py", "print('hello')")

        result = validate_execution_file(
            workspace.root,
            "hello.py",
        )

        assert result.is_file()


def test_missing_file_rejected():
    with AgentWorkspace() as workspace:
        with pytest.raises(FileNotFoundError):
            validate_execution_file(
                workspace.root,
                "missing.py",
            )


def test_path_traversal_rejected():
    with AgentWorkspace() as workspace:
        with pytest.raises(WorkspaceSecurityError):
            validate_execution_file(
                workspace.root,
                "../outside.py",
            )


def test_symlink_escape_rejected(tmp_path):
    outside = tmp_path / "outside.py"
    outside.write_text("print('outside')")

    with AgentWorkspace() as workspace:
        link = workspace.root / "escape.py"
        link.symlink_to(outside)

        with pytest.raises(WorkspaceSecurityError):
            validate_execution_file(
                workspace.root,
                "escape.py",
            )


def test_symlink_directory_rejected(tmp_path):
    outside = tmp_path / "external"
    outside.mkdir()
    (outside / "script.py").write_text("print('outside')")

    with AgentWorkspace() as workspace:
        (workspace.root / "linked").symlink_to(
            outside,
            target_is_directory=True,
        )

        with pytest.raises(WorkspaceSecurityError):
            validate_execution_file(
                workspace.root,
                "linked/script.py",
            )
