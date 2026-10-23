
from pathlib import Path

from app.tools.sandbox.docker_runner import (
    DockerSandboxRunner,
    ExecutionResult,
)
from app.tools.sandbox.policies import (
    build_execution_command,
    get_execution_policy,
)


class SandboxExecutionService:
    def execute(
        self,
        language: str,
        workspace: Path,
        filename: str,
    ) -> ExecutionResult:
        policy = get_execution_policy(language)
        command = build_execution_command(language, filename)

        runner = DockerSandboxRunner(
            image=policy.image,
            timeout_seconds=policy.timeout_seconds,
        )

        return runner.run(
            workspace=workspace,
            command=command,
        )
