
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal

from app.tools.sandbox.evidence import ExecutionEvidence
from app.tools.verifiers.base import VerificationResult


VerificationStatus = Literal["passed", "failed", "blocked"]


@dataclass(frozen=True)
class AgentVerificationReport:
    language: str
    static_result: VerificationResult
    execution_evidence: ExecutionEvidence | None
    status: VerificationStatus
    recorded_at: str
    source_sha256: str | None = None
    block_reason: str | None = None

    @property
    def approved_for_review(self) -> bool:
        return self.status == "passed"


def build_verification_report(
    language: str,
    static_result: VerificationResult,
    execution_evidence: ExecutionEvidence | None,
    source_sha256: str | None = None,
    block_reason: str | None = None,
) -> AgentVerificationReport:
    if block_reason is not None:
        status: VerificationStatus = "blocked"
    elif static_result.status == "unsupported":
        status = "blocked"
    elif not static_result.passed:
        status = "failed"
    elif execution_evidence is None:
        status = "blocked"
    elif execution_evidence.passed:
        status = "passed"
    else:
        status = "failed"

    return AgentVerificationReport(
        language=language,
        static_result=static_result,
        execution_evidence=execution_evidence,
        status=status,
        recorded_at=datetime.now(timezone.utc).isoformat(),
        source_sha256=source_sha256,
        block_reason=block_reason,
    )
