
from pathlib import Path

from app.services.agent_verification import (
    AgentVerificationReport,
    build_verification_report,
)
from app.tools.sandbox.execution_service import SandboxExecutionService
from app.tools.sandbox.snapshots import (
    managed_execution_snapshot,
    verify_snapshot_integrity,
)
from app.tools.verifiers.base import VerificationResult
from app.tools.verifiers.registry import verify_code


def blocked_report(
    source_sha256: str,
    reason: str,
) -> AgentVerificationReport:
    return build_verification_report(
        language="python",
        static_result=VerificationResult(
            language="python",
            status="unsupported",
            message=reason,
        ),
        execution_evidence=None,
        source_sha256=source_sha256,
        block_reason=reason,
    )


class VerificationCoordinator:
    def __init__(self):
        self.execution_service = SandboxExecutionService()

    def verify_python(
        self,
        workspace: Path,
        filename: str,
    ) -> tuple[AgentVerificationReport, str]:
        with managed_execution_snapshot(
            workspace,
            filename,
        ) as snapshot:
            source_hash = snapshot.sha256

            if not verify_snapshot_integrity(snapshot):
                return (
                    blocked_report(
                        source_hash,
                        "Snapshot integrity verification failed",
                    ),
                    source_hash,
                )

            source = snapshot.source_path.read_text(
                encoding="utf-8"
            )

            static_result = verify_code(
                language="python",
                source=source,
            )

            if not static_result.passed:
                return (
                    build_verification_report(
                        language="python",
                        static_result=static_result,
                        execution_evidence=None,
                        source_sha256=source_hash,
                    ),
                    source_hash,
                )

            if not verify_snapshot_integrity(snapshot):
                return (
                    blocked_report(
                        source_hash,
                        "Snapshot changed before execution",
                    ),
                    source_hash,
                )

            evidence = self.execution_service.execute_with_evidence(
                language="python",
                workspace=snapshot.root,
                filename=snapshot.filename,
            )

            if not verify_snapshot_integrity(snapshot):
                return (
                    blocked_report(
                        source_hash,
                        "Snapshot changed during execution",
                    ),
                    source_hash,
                )

            return (
                build_verification_report(
                    language="python",
                    static_result=static_result,
                    execution_evidence=evidence,
                    source_sha256=source_hash,
                ),
                source_hash,
            )
