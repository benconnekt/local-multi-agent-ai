
import hashlib
import shutil

import pytest

from app.tools.sandbox.snapshots import (
    create_execution_snapshot,
)
from app.tools.sandbox.workspace_security import (
    WorkspaceSecurityError,
)
from app.tools.workspace import AgentWorkspace


def test_snapshot_preserves_original_content():
    with AgentWorkspace() as workspace:
        workspace.write_file(
            "hello.py",
            "print('original')",
        )

        snapshot = create_execution_snapshot(
            workspace.root,
            "hello.py",
        )

        try:
            workspace.write_file(
                "hello.py",
                "print('modified')",
            )

            assert (
                snapshot.source_path.read_text()
                == "print('original')"
            )

            assert snapshot.sha256 == hashlib.sha256(
                b"print('original')"
            ).hexdigest()

        finally:
            shutil.rmtree(snapshot.root)


def test_snapshot_rejects_symlinks(tmp_path):
    outside = tmp_path / "outside.py"
    outside.write_text("print('outside')")

    workspace = tmp_path / "workspace"
    workspace.mkdir()

    (workspace / "linked.py").symlink_to(outside)

    with pytest.raises(WorkspaceSecurityError):
        create_execution_snapshot(
            workspace,
            "linked.py",
        )


def test_snapshot_rejects_path_traversal(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    with pytest.raises(WorkspaceSecurityError):
        create_execution_snapshot(
            workspace,
            "../outside.py",
        )


def test_snapshot_rejects_oversized_files(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    (workspace / "large.py").write_bytes(
        b"x" * (1024 * 1024 + 1)
    )

    with pytest.raises(WorkspaceSecurityError):
        create_execution_snapshot(
            workspace,
            "large.py",
        )
