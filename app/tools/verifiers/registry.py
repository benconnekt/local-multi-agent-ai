
from app.tools.code_extractor import normalize_language
from app.tools.verifiers.base import VerificationResult
from app.tools.verifiers.python import PythonVerifier
from app.tools.verifiers.typescript import TypeScriptVerifier


VERIFIERS = {
    "python": PythonVerifier(),
    "typescript": TypeScriptVerifier(),
}


def verify_code(
    language: str,
    source: str,
) -> VerificationResult:
    normalized = normalize_language(language)

    verifier = VERIFIERS.get(normalized)

    if verifier is None:
        return VerificationResult(
            language=normalized,
            status="unsupported",
            message=f"No verifier registered for language: {normalized}",
        )

    return verifier.verify(source)
