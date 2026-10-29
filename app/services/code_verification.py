
from dataclasses import dataclass

from app.tools.code_extractor import (
    extract_code,
    normalize_language,
)
from app.tools.verifiers.registry import verify_code
from app.tools.workspace import AgentWorkspace


@dataclass(frozen=True)
class CodeVerificationResult:
    passed: bool
    code: str
    message: str


def verify_generated_code(
    response: str,
    workspace: AgentWorkspace,
    filename: str = "generated.py",
    language: str = "python",
) -> CodeVerificationResult:
    normalized = normalize_language(language)

    try:
        code = extract_code(response, normalized)
    except ValueError as exc:
        return CodeVerificationResult(
            passed=False,
            code="",
            message=str(exc),
        )

    if not code:
        return CodeVerificationResult(
            passed=False,
            code="",
            message="No source code was generated.",
        )

    result = verify_code(normalized, code)

    if not result.passed:
        return CodeVerificationResult(
            passed=False,
            code=code,
            message=result.message,
        )

    workspace.write_file(filename, code)

    return CodeVerificationResult(
        passed=True,
        code=code,
        message=(
            f"{normalized} verification passed "
            "and file saved."
        ),
    )
