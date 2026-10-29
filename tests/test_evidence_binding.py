
from app.services.agent_verification import build_verification_report
from app.tools.verifiers.base import VerificationResult


def test_explicit_block_reason_prevents_approval():
    report = build_verification_report(
        language="python",
        static_result=VerificationResult(
            language="python",
            status="passed",
            message="Syntax valid",
        ),
        execution_evidence=None,
        source_sha256="a" * 64,
        block_reason="Snapshot integrity failed",
    )

    assert report.status == "blocked"
    assert not report.approved_for_review
    assert report.source_sha256 == "a" * 64
    assert report.block_reason == "Snapshot integrity failed"


def test_missing_execution_evidence_remains_blocked():
    report = build_verification_report(
        language="python",
        static_result=VerificationResult(
            language="python",
            status="passed",
            message="Syntax valid",
        ),
        execution_evidence=None,
        source_sha256="b" * 64,
    )

    assert report.status == "blocked"
    assert report.source_sha256 == "b" * 64


def test_static_failure_retains_source_hash():
    report = build_verification_report(
        language="python",
        static_result=VerificationResult(
            language="python",
            status="failed",
            message="Invalid syntax",
        ),
        execution_evidence=None,
        source_sha256="c" * 64,
    )

    assert report.status == "failed"
    assert report.source_sha256 == "c" * 64
    assert not report.approved_for_review
