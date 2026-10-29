
from app.services.agent_verification import build_verification_report
from app.tools.sandbox.docker_runner import ExecutionResult
from app.tools.sandbox.evidence import build_execution_evidence
from app.tools.verifiers.base import VerificationResult
from app.tools.sandbox.policies import get_execution_policy


def make_evidence(exit_code=0, cleanup=True):
    result = ExecutionResult(
        exit_code=exit_code,
        stdout="ok" if exit_code == 0 else "",
        stderr="" if exit_code == 0 else "error",
        duration_seconds=0.2,
        timed_out=False,
        container_name="agent-run-test",
        cleanup_succeeded=cleanup,
    )

    return build_execution_evidence(
        get_execution_policy("python"),
        ["python", "-B", "hello.py"],
        result,
    )


def test_all_checks_pass():
    report = build_verification_report(
        "python",
        VerificationResult("python", "passed", "Syntax valid"),
        make_evidence(),
    )

    assert report.status == "passed"
    assert report.approved_for_review


def test_static_failure():
    report = build_verification_report(
        "python",
        VerificationResult("python", "failed", "Syntax error"),
        make_evidence(),
    )

    assert report.status == "failed"
    assert not report.approved_for_review


def test_missing_execution_evidence():
    report = build_verification_report(
        "python",
        VerificationResult("python", "passed", "Syntax valid"),
        None,
    )

    assert report.status == "blocked"


def test_unsupported_verifier():
    report = build_verification_report(
        "ruby",
        VerificationResult("ruby", "unsupported", "Not supported"),
        None,
    )

    assert report.status == "blocked"


def test_execution_failure():
    report = build_verification_report(
        "python",
        VerificationResult("python", "passed", "Syntax valid"),
        make_evidence(exit_code=1),
    )

    assert report.status == "failed"


def test_cleanup_failure():
    report = build_verification_report(
        "python",
        VerificationResult("python", "passed", "Syntax valid"),
        make_evidence(cleanup=False),
    )

    assert report.status == "failed"
