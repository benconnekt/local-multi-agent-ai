
import ast
from dataclasses import dataclass


@dataclass(frozen=True)
class SyntaxResult:
    passed: bool
    message: str


def verify_python_syntax(source: str) -> SyntaxResult:
    try:
        ast.parse(source)
        return SyntaxResult(
            passed=True,
            message="Python syntax is valid.",
        )
    except SyntaxError as exc:
        return SyntaxResult(
            passed=False,
            message=(
                f"Syntax error at line {exc.lineno}: "
                f"{exc.msg}"
            ),
        )
