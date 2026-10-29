
from app.tools.python_verifier import verify_python_syntax
from app.tools.verifiers.base import VerificationResult


class PythonVerifier:
    def verify(self, source: str) -> VerificationResult:
        result = verify_python_syntax(source)

        return VerificationResult(
            language="python",
            status="passed" if result.passed else "failed",
            message=result.message,
        )
