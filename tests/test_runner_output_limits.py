
from app.tools.sandbox.docker_runner import (
    DockerSandboxRunner,
    MAX_OUTPUT_BYTES,
)
from app.tools.sandbox.policies import get_execution_policy
from app.tools.workspace import AgentWorkspace


def test_stdout_is_bounded(docker_available):
    with AgentWorkspace() as workspace:
        workspace.write_file(
            "large.py",
            "print('A' * 100000)",
        )

        runner = DockerSandboxRunner(
            get_execution_policy("python")
        )

        result = runner.run(
            workspace.root,
            ["python", "-B", "large.py"],
        )

        assert result.passed
        assert len(result.stdout.encode("utf-8")) <= MAX_OUTPUT_BYTES


def test_stderr_is_bounded(docker_available):
    with AgentWorkspace() as workspace:
        workspace.write_file(
            "error.py",
            "import sys\n"
            "sys.stderr.write('E' * 100000)\n",
        )

        runner = DockerSandboxRunner(
            get_execution_policy("python")
        )

        result = runner.run(
            workspace.root,
            ["python", "-B", "error.py"],
        )

        assert result.passed
        assert len(result.stderr.encode("utf-8")) <= MAX_OUTPUT_BYTES
