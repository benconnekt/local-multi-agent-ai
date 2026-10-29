
import os
import signal
import subprocess
import threading
import time
import uuid

from dataclasses import dataclass, field
from pathlib import Path

from app.tools.sandbox.policies import (
    ExecutionPolicy,
    validate_execution_policy,
    validate_execution_command,
)


MAX_OUTPUT_BYTES = 10_000
READ_CHUNK_SIZE = 4096
CLEANUP_TIMEOUT_SECONDS = 10
OUTPUT_THREAD_JOIN_TIMEOUT_SECONDS = 2


@dataclass(frozen=True)
class ExecutionResult:
    exit_code: int | None
    stdout: str
    stderr: str
    duration_seconds: float
    timed_out: bool
    container_name: str
    cleanup_succeeded: bool
    output_capture_succeeded: bool = True

    @property
    def passed(self) -> bool:
        return (
            self.exit_code == 0
            and not self.timed_out
            and self.cleanup_succeeded
            and self.output_capture_succeeded
        )


@dataclass
class OutputCaptureState:
    errors: list[str] = field(default_factory=list)


def _drain_stream(
    stream,
    buffer: bytearray,
    limit: int,
    state: OutputCaptureState,
) -> None:
    """
    Drain a process stream without retaining unlimited output.

    Output beyond the configured limit is discarded, but
    the stream continues to be consumed to avoid blocking
    the child process.

    Any read or close errors are recorded so execution
    cannot be approved with incomplete output evidence.
    """
    try:
        while True:
            chunk = stream.read(READ_CHUNK_SIZE)

            if not chunk:
                break

            remaining = limit - len(buffer)

            if remaining > 0:
                buffer.extend(chunk[:remaining])

    except Exception as exc:
        state.errors.append(
            f"{type(exc).__name__}: {exc}"
        )

    finally:
        try:
            stream.close()
        except Exception as exc:
            state.errors.append(
                f"Stream close failed: "
                f"{type(exc).__name__}: {exc}"
            )



def _cleanup_container(container_name: str) -> bool:
    """
    Remove the container if it exists, then verify
    that Docker reports no matching container.

    A Docker command failure is not automatically
    treated as successful cleanup.
    """
    try:
        removal = subprocess.run(
            [
                "docker",
                "rm",
                "-f",
                container_name,
            ],
            capture_output=True,
            text=True,
            timeout=CLEANUP_TIMEOUT_SECONDS,
            check=False,
        )

        inspection = subprocess.run(
            [
                "docker",
                "ps",
                "-a",
                "--filter",
                f"name=^{container_name}$",
                "--format",
                "{{.Names}}",
            ],
            capture_output=True,
            text=True,
            timeout=CLEANUP_TIMEOUT_SECONDS,
            check=False,
        )

        return (
            inspection.returncode == 0
            and inspection.stdout.strip() == ""
        )

    except (
        subprocess.TimeoutExpired,
        OSError,
    ):
        return False

class DockerSandboxRunner:
    """
    Executes approved commands inside restricted Docker
    containers and returns structured execution evidence.

    This runner is not yet a complete security boundary
    for arbitrary untrusted code.
    """

    def __init__(self, policy: ExecutionPolicy):
        if policy.timeout_seconds <= 0:
            raise ValueError(
                "Timeout must be positive"
            )

        if policy.memory_mb <= 0:
            raise ValueError(
                "Memory limit must be positive"
            )

        if policy.cpus <= 0:
            raise ValueError(
                "CPU limit must be positive"
            )

        validate_execution_policy(policy)

        self.policy = policy

    def run(
        self,
        workspace: Path,
        command: list[str],
    ) -> ExecutionResult:
        workspace = Path(workspace).resolve()

        if not workspace.is_dir():
            raise ValueError(
                "Workspace directory does not exist"
            )

        validate_execution_command(
            self.policy,
            command,
        )

        if not command:
            raise ValueError(
                "Execution command cannot be empty"
            )

        container_name = (
            f"agent-run-{uuid.uuid4().hex}"
        )

        started = time.monotonic()

        docker_command = [
            "docker",
            "run",
            "--rm",
            "--name",
            container_name,
            "--pull",
            "never",
            "--network",
            "none",
            "--read-only",
            "--cap-drop",
            "ALL",
            "--security-opt",
            "no-new-privileges",
            "--pids-limit",
            "64",
            "--memory",
            f"{self.policy.memory_mb}m",
            "--cpus",
            str(self.policy.cpus),
            "--user",
            "65534:65534",
            "--mount",
            (
                f"type=bind,"
                f"src={workspace},"
                f"dst=/workspace,"
                f"readonly"
            ),
            "--workdir",
            "/workspace",
            "--tmpfs",
            "/tmp:rw,noexec,nosuid,size=32m",
            self.policy.image,
            *command,
        ]

        exit_code: int | None = None
        timed_out = False
        cleanup_succeeded = False
        output_capture_succeeded = False

        stdout_buffer = bytearray()
        stderr_buffer = bytearray()

        capture_state = OutputCaptureState()

        process: subprocess.Popen | None = None
        threads: list[threading.Thread] = []

        try:
            process = subprocess.Popen(
                docker_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True,
            )

            if (
                process.stdout is None
                or process.stderr is None
            ):
                raise RuntimeError(
                    "Failed to initialise Docker output pipes"
                )

            threads = [
                threading.Thread(
                    target=_drain_stream,
                    args=(
                        process.stdout,
                        stdout_buffer,
                        MAX_OUTPUT_BYTES,
                        capture_state,
                    ),
                    daemon=True,
                    name=f"{container_name}-stdout",
                ),
                threading.Thread(
                    target=_drain_stream,
                    args=(
                        process.stderr,
                        stderr_buffer,
                        MAX_OUTPUT_BYTES,
                        capture_state,
                    ),
                    daemon=True,
                    name=f"{container_name}-stderr",
                ),
            ]

            for thread in threads:
                thread.start()

            try:
                exit_code = process.wait(
                    timeout=self.policy.timeout_seconds
                )

            except subprocess.TimeoutExpired:
                timed_out = True

                try:
                    os.killpg(
                        process.pid,
                        signal.SIGKILL,
                    )

                except ProcessLookupError:
                    pass

                # Reap the Docker CLI process.
                process.wait()

        finally:
            cleanup_succeeded = _cleanup_container(
                container_name
            )

            for thread in threads:
                thread.join(
                    timeout=OUTPUT_THREAD_JOIN_TIMEOUT_SECONDS
                )

            output_capture_succeeded = (
                len(threads) == 2
                and all(
                    not thread.is_alive()
                    for thread in threads
                )
                and not capture_state.errors
            )

        stdout = stdout_buffer.decode(
            "utf-8",
            errors="replace",
        )

        stderr = stderr_buffer.decode(
            "utf-8",
            errors="replace",
        )

        return ExecutionResult(
            exit_code=exit_code,
            stdout=stdout,
            stderr=stderr,
            duration_seconds=(
                time.monotonic() - started
            ),
            timed_out=timed_out,
            container_name=container_name,
            cleanup_succeeded=cleanup_succeeded,
            output_capture_succeeded=output_capture_succeeded,
        )
