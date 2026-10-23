
from dataclasses import dataclass
from pathlib import PurePosixPath


@dataclass(frozen=True)
class ExecutionPolicy:
    language: str
    image: str
    executable: str
    timeout_seconds: int
    memory_mb: int
    cpus: float


POLICIES = {
    "python": ExecutionPolicy(
        language="python",
        image="python:3.12-slim",
        executable="python",
        timeout_seconds=15,
        memory_mb=256,
        cpus=1.0,
    ),
    "typescript": ExecutionPolicy(
    language="typescript",
    image="node:24-slim",
    executable="node",
    timeout_seconds=20,
    memory_mb=512,
    cpus=1.0,
),
}


LANGUAGE_ALIASES = {
    "py": "python",
    "python3": "python",
    "ts": "typescript",
}


def get_execution_policy(language: str) -> ExecutionPolicy:
    normalized = language.strip().lower()
    normalized = LANGUAGE_ALIASES.get(normalized, normalized)

    policy = POLICIES.get(normalized)

    if policy is None:
        raise ValueError(
            f"Unsupported execution language: {language}"
        )

    return policy


def build_execution_command(
    language: str,
    filename: str,
) -> list[str]:
    policy = get_execution_policy(language)

    path = PurePosixPath(filename)

    if (
        path.is_absolute()
        or ".." in path.parts
        or not filename
        or "\\" in filename
        or path.suffix not in {".py", ".js"}
    ):
        raise ValueError("Invalid execution filename")

    if policy.language == "python":
        if path.suffix != ".py":
            raise ValueError("Python execution requires a .py file")

        return ["python", "-B", str(path)]

    if policy.language == "typescript":
        # TypeScript must first be compiled into trusted
        # workspace output. We execute the resulting JavaScript.
        if path.suffix != ".js":
            raise ValueError(
                "TypeScript execution requires compiled .js"
            )

        return ["node", str(path)]

    raise ValueError("Unsupported execution policy")
