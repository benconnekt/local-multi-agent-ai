
import os
import signal
import subprocess
import time
import uuid
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ExecutionResult:
    exit_code: int | None
    stdout: str
    stderr: str
    duration_seconds: float
    timed_out: bool
    container_name: str
    cleanup_succeeded: bool

    @property
    def passed(self) -> bool:
        return (
            self.exit_code == 0
            and not self.timed_out
            and self.cleanup_succeeded
        )


class DockerSandboxRunner:
    def __init__(
        self,
        image: str = "python:3.12-slim",
        timeout_seconds: int = 15,
    ):
        if timeout_seconds <= 0:
            raise ValueError("Timeout must be positive")

        self.image = image
        self.timeout_seconds = timeout_seconds

    def run(
        self,
        workspace: Path,
        command: list[str],
    ) -> ExecutionResult:
        workspace = Path(workspace).resolve()

        if not workspace.is_dir():
            raise ValueError("Workspace directory does not exist")

        if not command:
            raise ValueError("Execution command cannot be empty")

        container_name = f"agent-run-{uuid.uuid4().hex}"
        started = time.monotonic()

        docker_command = [
            "docker", "run", "--rm",
            "--name", container_name,
            "--pull", "never",
            "--network", "none",
            "--read-only",
            "--cap-drop", "ALL",
            "--security-opt", "no-new-privileges",
            "--pids-limit", "64",
            "--memory", "256m",
            "--cpus", "1",
            "--user", "65534:65534",
            "--mount",
            f"type=bind,src={workspace},dst=/workspace,readonly",
            "--workdir", "/workspace",
            "--tmpfs", "/tmp:rw,noexec,nosuid,size=32m",
            self.image,
            *command,
        ]

        exit_code = None
        stdout = ""
        stderr = ""
        timed_out = False
        cleanup_succeeded = False
        process = None

        try:
            process = subprocess.Popen(
                docker_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                start_new_session=True,
            )

            try:
                stdout, stderr = process.communicate(
                    timeout=self.timeout_seconds
                )
                exit_code = process.returncode

            except subprocess.TimeoutExpired:
                timed_out = True

                os.killpg(process.pid, signal.SIGKILL)
                stdout, stderr = process.communicate()

        finally:
            # Remove the container even when execution fails.
            # The name is generated internally, never by an agent.
            try:
                cleanup = subprocess.run(
                    ["docker", "rm", "-f", container_name],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    check=False,
                )

                # Docker --rm may have already removed it.
                cleanup_succeeded = (
                    cleanup.returncode == 0
                    or "No such container" in cleanup.stderr
                )

            except (subprocess.TimeoutExpired, OSError):
                cleanup_succeeded = False

        return ExecutionResult(
            exit_code=exit_code,
            stdout=stdout[:10000],
            stderr=stderr[:10000],
            duration_seconds=time.monotonic() - started,
            timed_out=timed_out,
            container_name=container_name,
            cleanup_succeeded=cleanup_succeeded,
        )
