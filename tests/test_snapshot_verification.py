
import pytest

from app.services.verification_coordinator import (
    VerificationCoordinator,
)
from app.tools.sandbox.snapshots import (
    managed_execution_snapshot,
    verify_snapshot_integrity,
)
from app.tools.workspace import AgentWorkspace


def test_snapshot_is_independent_of_original_workspace():
    with AgentWorkspace() as workspace:
        workspace.write_file(
            "hello.py",
            "print('original')",
        )

        with managed_execution_snapshot(
            workspace.root,
            "hello.py",
        ) as snapshot:
            workspace.write_file(
                "hello.py",
                "print('modified')",
            )

            assert snapshot.source_path.read_text() == (
                "print('original')"
            )

            assert verify_snapshot_integrity(snapshot)


def test_snapshot_detects_tampering():
    with AgentWorkspace() as workspace:
        workspace.write_file(
            "hello.py",
            "print('original')",
        )

        with managed_execution_snapshot(
            workspace.root,
            "hello.py",
        ) as snapshot:
            snapshot.source_path.chmod(0o644)
            snapshot.source_path.write_text(
                "print('tampered')"
            )

            assert not verify_snapshot_integrity(snapshot)


def test_snapshot_cleanup():
    with AgentWorkspace() as workspace:
        workspace.write_file(
            "hello.py",
            "print('hello')",
        )

        with managed_execution_snapshot(
            workspace.root,
            "hello.py",
        ) as snapshot:
            snapshot_root = snapshot.root
            assert snapshot_root.exists()

        assert not snapshot_root.exists()


def test_coordinator_executes_snapshot(docker_available):
    coordinator = VerificationCoordinator()

    with AgentWorkspace() as workspace:
        workspace.write_file(
            "hello.py",
            "print('snapshot verified')",
        )

        report, source_hash = coordinator.verify_python(
            workspace.root,
            "hello.py",
        )

        assert report.status == "passed"
        assert report.execution_evidence is not None
        assert (
            "snapshot verified"
            in report.execution_evidence.stdout
        )
        assert len(source_hash) == 64


def test_invalid_python_never_executes():
    coordinator = VerificationCoordinator()

    with AgentWorkspace() as workspace:
        workspace.write_file(
            "broken.py",
            "def broken(:\n    pass",
        )

        report, _ = coordinator.verify_python(
            workspace.root,
            "broken.py",
        )

        assert report.status == "failed"
        assert report.execution_evidence is None
