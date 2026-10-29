
from app.tools.sandbox.docker_runner import ExecutionResult
from app.tools.sandbox.evidence import build_execution_evidence
from app.tools.sandbox.policies import get_execution_policy


def test_successful_execution_evidence():
    result = ExecutionResult(
        exit_code=0,
        stdout="5\n",
        stderr="",
        duration_seconds=0.25,
        timed_out=False,
        container_name="agent-run-test",
        cleanup_succeeded=True,
    )

    evidence = build_execution_evidence(
        policy=get_execution_policy("python"),
        command=["python", "-B", "hello.py"],
        result=result,
    )

    assert evidence.passed
    assert evidence.exit_code == 0
    assert evidence.stdout == "5\n"
    assert evidence.language == "python"
    assert evidence.cleanup_succeeded


def test_failed_execution_evidence():
    result = ExecutionResult(
        exit_code=1,
        stdout="",
        stderr="ValueError",
        duration_seconds=0.1,
        timed_out=False,
        container_name="agent-run-test",
        cleanup_succeeded=True,
    )

    evidence = build_execution_evidence(
        policy=get_execution_policy("python"),
        command=["python", "-B", "hello.py"],
        result=result,
    )

    assert not evidence.passed
    assert evidence.exit_code == 1
    assert evidence.stderr == "ValueError"
