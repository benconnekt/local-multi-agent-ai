
from dataclasses import replace
from unittest.mock import patch

from app.tools.sandbox.docker_runner import (
    DockerSandboxRunner,
    ExecutionResult,
    _cleanup_container,
)
from app.tools.sandbox.policies import get_execution_policy
from app.tools.workspace import AgentWorkspace


def test_failed_output_capture_blocks_approval():
    result = ExecutionResult(
        exit_code=0,
        stdout="OK",
        stderr="",
        duration_seconds=0.1,
        timed_out=False,
        container_name="test-container",
        cleanup_succeeded=True,
        output_capture_succeeded=False,
    )

    assert not result.passed


def test_cleanup_fails_closed_on_docker_error():
    with patch(
        "app.tools.sandbox.docker_runner.subprocess.run",
        side_effect=OSError("Docker unavailable"),
    ):
        assert not _cleanup_container("test-container")


def test_cleanup_fails_closed_on_timeout():
    import subprocess

    with patch(
        "app.tools.sandbox.docker_runner.subprocess.run",
        side_effect=subprocess.TimeoutExpired(
            cmd="docker",
            timeout=10,
        ),
    ):
        assert not _cleanup_container("test-container")


def test_runner_passes_output_capture_status(docker_available):
    runner = DockerSandboxRunner(
        get_execution_policy("python")
    )

    with AgentWorkspace() as workspace:
        workspace.write_file(
            "example.py",
            "print('ready')",
        )

        result = runner.run(
            workspace.root,
            ["python", "-B", "example.py"],
        )

        assert result.passed
        assert result.output_capture_succeeded
