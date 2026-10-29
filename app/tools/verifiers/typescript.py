
import shutil
import subprocess
import tempfile
from pathlib import Path

from app.tools.verifiers.base import VerificationResult


PROJECT_ROOT = Path(__file__).resolve().parents[3]


def resolve_tsc() -> str | None:
    local_tsc = PROJECT_ROOT / "node_modules" / ".bin" / "tsc"

    if local_tsc.is_file():
        return str(local_tsc)

    return shutil.which("tsc")


class TypeScriptVerifier:
    def verify(self, source: str) -> VerificationResult:
        compiler = resolve_tsc()

        if compiler is None:
            return VerificationResult(
                language="typescript",
                status="unsupported",
                message="TypeScript compiler (tsc) not found.",
            )

        with tempfile.TemporaryDirectory(
            prefix="agent-ts-check-"
        ) as directory:
            source_file = Path(directory) / "generated.ts"
            source_file.write_text(source, encoding="utf-8")

            try:
                result = subprocess.run(
                    [
                        compiler,
                        "--noEmit",
                        "--strict",
                        "--skipLibCheck",
                        "--target",
                        "ES2020",
                        "--module",
                        "commonjs",
                        str(source_file),
                    ],
                    capture_output=True,
                    text=True,
                    timeout=15,
                    check=False,
                    cwd=directory,
                )

            except (FileNotFoundError, PermissionError) as exc:
                return VerificationResult(
                    language="typescript",
                    status="unsupported",
                    message=f"Unable to launch TypeScript compiler: {exc}",
                )

            except subprocess.TimeoutExpired:
                return VerificationResult(
                    language="typescript",
                    status="failed",
                    message="TypeScript verification timed out.",
                )

            if result.returncode == 0:
                return VerificationResult(
                    language="typescript",
                    status="passed",
                    message="TypeScript compiler checks passed.",
                )

            return VerificationResult(
                language="typescript",
                status="failed",
                message=(
                    result.stdout.strip()
                    or result.stderr.strip()
                    or f"TypeScript exited with code {result.returncode}."
                )[:2000],
            )
