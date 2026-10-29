
from pathlib import Path, PurePosixPath


class WorkspaceSecurityError(ValueError):
    pass


def validate_execution_file(
    workspace: Path,
    filename: str,
) -> Path:
    root = Path(workspace).resolve(strict=True)

    if not root.is_dir() or root.is_symlink():
        raise WorkspaceSecurityError("Invalid workspace")

    if not filename or "\x00" in filename or "\\" in filename:
        raise WorkspaceSecurityError("Invalid filename")

    relative = PurePosixPath(filename)

    if (
        relative.is_absolute()
        or ".." in relative.parts
        or "." in relative.parts
    ):
        raise WorkspaceSecurityError("Unsafe file path")

    candidate = root.joinpath(*relative.parts)

    # Reject symlinks in the selected path, including directories.
    current = root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise WorkspaceSecurityError("Symlink paths are not allowed")

    resolved = candidate.resolve(strict=True)

    if not resolved.is_relative_to(root):
        raise WorkspaceSecurityError("File escapes workspace")

    if not resolved.is_file():
        raise WorkspaceSecurityError("Execution target is not a file")

    return resolved
