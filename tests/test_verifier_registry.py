
from app.tools.verifiers.registry import verify_code


def test_python_verifier_passes_valid_code():
    result = verify_code(
        "python",
        "def add(a, b): return a + b",
    )
    assert result.passed


def test_python_verifier_rejects_invalid_code():
    result = verify_code(
        "python",
        "def add(a, b) return a + b",
    )
    assert result.status == "failed"


def test_typescript_verifier_passes_valid_code():
    result = verify_code(
        "typescript",
        "function add(a: number, b: number): number { return a + b; }",
    )
    assert result.passed, result.message


def test_typescript_verifier_rejects_invalid_code():
    result = verify_code(
        "typescript",
        "const value: number = 'hello';",
    )
    assert result.status == "failed"


def test_unsupported_language_is_not_approved():
    result = verify_code(
        "rust",
        "fn main() {}",
    )
    assert result.status == "unsupported"
    assert not result.passed


def test_language_alias():
    result = verify_code(
        "TS",
        "const value: number = 42;",
    )
    assert result.passed, result.message
