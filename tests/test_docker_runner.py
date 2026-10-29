
from app.tools.sandbox.docker_runner import DockerSandboxRunner
from app.tools.workspace import AgentWorkspace

from app.tools.sandbox.policies import get_execution_policy
from conftest import docker_available;


def test_python_execution_passes(docker_available):
    runner = DockerSandboxRunner(
        policy=get_execution_policy("python")
    )

    with AgentWorkspace() as workspace:
        workspace.write_file(
            "example.py",
            "print(2 + 3)",
        )

        result = runner.run(
            workspace.root,
            ["python", "-B", "example.py"],
        )

        assert result.passed, result.stderr
        assert result.stdout.strip() == "5"


def test_python_execution_failure(docker_available):
    runner = DockerSandboxRunner(
        policy=get_execution_policy("python")
    )

    with AgentWorkspace() as workspace:
        workspace.write_file(
            "example.py",
            "raise ValueError('expected failure')",
        )

        result = runner.run(
            workspace.root,
            ["python", "-B", "example.py"],
        )

        assert not result.passed
        assert "ValueError" in result.stderr


def test_python_execution_timeout(docker_available):
    runner = DockerSandboxRunner(policy=get_execution_policy("python") )

    with AgentWorkspace() as workspace:
        workspace.write_file(
            "example.py",
            "while True:\n    pass",
        )

        result = runner.run(
            workspace.root,
            ["python", "-B", "example.py"],
        )

        assert result.timed_out
        assert not result.passed


import subprocess


def test_timeout_removes_container(docker_available): 
    runner = DockerSandboxRunner(policy=get_execution_policy("python") )

    with AgentWorkspace() as workspace:
        workspace.write_file(
            "infinite.py",
            "while True:\n    pass\n",
        )

        result = runner.run(
            workspace.root,
            ["python", "-B", "infinite.py"],
        )

        assert result.timed_out
        assert not result.passed
        assert result.cleanup_succeeded

        inspection = subprocess.run(
            [
                "docker", "ps", "-a",
                "--filter",
                f"name=^{result.container_name}$",
                "--format", "{{.Names}}",
            ],
            capture_output=True,
            text=True,
            check=True,
            timeout=10,
        )

        assert inspection.stdout.strip() == ""

