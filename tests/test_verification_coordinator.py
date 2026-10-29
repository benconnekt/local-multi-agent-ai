
from app.services.verification_coordinator import VerificationCoordinator
from app.tools.workspace import AgentWorkspace


def test_valid_python_verification(docker_available):
    coordinator = VerificationCoordinator()

    with AgentWorkspace() as workspace:
        workspace.write_file(
            "hello.py",
            "print('verified')",
        )

        report, source_hash = coordinator.verify_python(
            workspace.root,
            "hello.py",
        )

        assert report.status == "passed"
        assert report.execution_evidence is not None
        assert len(source_hash) == 64


def test_invalid_python_does_not_execute():
    coordinator = VerificationCoordinator()

    with AgentWorkspace() as workspace:
        workspace.write_file(
            "broken.py",
            "def broken(:\n    pass",
        )

        report, source_hash = coordinator.verify_python(
            workspace.root,
            "broken.py",
        )

        assert report.status == "failed"
        assert report.execution_evidence is None
        assert len(source_hash) == 64
