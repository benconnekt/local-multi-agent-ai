
from pathlib import Path

from app.tools.sandbox.docker_runner import (
    DockerSandboxRunner,
    ExecutionResult,
)
from app.tools.sandbox.policies import (
    build_execution_command,
    get_execution_policy,
)

from app.tools.sandbox.workspace_security import (
    validate_execution_file,
)

from app.tools.sandbox.evidence import (
    ExecutionEvidence,
    build_execution_evidence,
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

        runner = DockerSandboxRunner(policy=policy)

        validate_execution_file(workspace, filename)

        return runner.run(
            workspace=workspace,
            command=command,
        )

    
    def execute_with_evidence(
        self,
        language: str,
        workspace: Path,
        filename: str,
    ) -> ExecutionEvidence:
        policy = get_execution_policy(language)
        command = build_execution_command(language, filename)

        result = self.execute(
            language=language,
            workspace=workspace,
            filename=filename,
        )

        return build_execution_evidence(
            policy=policy,
            command=command,
            result=result,
        )

