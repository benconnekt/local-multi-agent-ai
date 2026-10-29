
from dataclasses import dataclass
from datetime import datetime, timezone

from app.tools.sandbox.docker_runner import ExecutionResult
from app.tools.sandbox.policies import ExecutionPolicy


@dataclass(frozen=True)
class ExecutionEvidence:
    language: str
    image: str
    command: tuple[str, ...]
    exit_code: int | None
    stdout: str
    stderr: str
    duration_seconds: float
    timed_out: bool
    cleanup_succeeded: bool
    passed: bool
    recorded_at: str


def build_execution_evidence(
    policy: ExecutionPolicy,
    command: list[str],
    result: ExecutionResult,
) -> ExecutionEvidence:
    return ExecutionEvidence(
        language=policy.language,
        image=policy.image,
        command=tuple(command),
        exit_code=result.exit_code,
        stdout=result.stdout,
        stderr=result.stderr,
        duration_seconds=result.duration_seconds,
        timed_out=result.timed_out,
        cleanup_succeeded=result.cleanup_succeeded,
        passed=result.passed,
        recorded_at=datetime.now(timezone.utc).isoformat(),
    )
