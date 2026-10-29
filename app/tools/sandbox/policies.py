
from dataclasses import dataclass
from pathlib import PurePosixPath

import re


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
        image=(
            "python:3.12-slim@sha256:"
            "a0f57064cbdcd6285fa45f51237ab0b35ea8ebaed06a1f5973e89e19dfb86704"
        ),
        executable="python",
        timeout_seconds=15,
        memory_mb=256,
        cpus=1.0,
    ),
    "typescript": ExecutionPolicy(
        language="typescript",
        image=(
            "node:24-slim@sha256:"
            "55fb5f5a527ea2c5c4a95f963e48ef90aa38c7b346054fdc8ee9957a2b55d205"
        ),
        executable="node",
        timeout_seconds=20,
        memory_mb=512,
        cpus=1.0,
    ),
}

PINNED_IMAGE_PATTERN = re.compile(
    r"^[a-z0-9][a-z0-9._/-]*"
    r"(?::[a-zA-Z0-9._-]+)?"
    r"@sha256:[a-f0-9]{64}$"
)


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

    validate_pinned_image(policy.image)

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

def validate_pinned_image(image: str) -> None:
    if not PINNED_IMAGE_PATTERN.fullmatch(image):
        raise ValueError(
            f"Docker image must be SHA-256 pinned: {image}"
        )


def validate_execution_policy(policy: ExecutionPolicy) -> None:
    approved = get_execution_policy(policy.language)

    if policy != approved:
        raise ValueError(
            "Execution policy does not match approved configuration"
        )

    validate_pinned_image(policy.image)


from pathlib import PurePosixPath


def validate_execution_command(
    policy: ExecutionPolicy,
    command: list[str],
) -> None:
    validate_execution_policy(policy)

    if not isinstance(command, list):
        raise ValueError("Execution command must be a list")

    if len(command) != 3 and policy.language == "python":
        raise ValueError("Invalid Python execution command")

    if len(command) != 2 and policy.language == "typescript":
        raise ValueError("Invalid Node execution command")

    if policy.language == "python":
        if command[:2] != ["python", "-B"]:
            raise ValueError("Unapproved Python command")

        filename = command[2]
        expected_suffix = ".py"

    elif policy.language == "typescript":
        if command[0] != "node":
            raise ValueError("Unapproved Node command")

        filename = command[1]
        expected_suffix = ".js"

    else:
        raise ValueError("Unsupported execution language")

    if not isinstance(filename, str):
        raise ValueError("Invalid execution filename")

    path = PurePosixPath(filename)

    if (
        not filename
        or "\x00" in filename
        or "\\" in filename
        or path.is_absolute()
        or ".." in path.parts
        or path.suffix != expected_suffix
    ):
        raise ValueError("Unsafe execution filename")


