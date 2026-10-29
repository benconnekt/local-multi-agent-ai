
import hashlib
import os
import stat
import tempfile
from dataclasses import dataclass
from pathlib import Path

from app.tools.sandbox.workspace_security import (
    WorkspaceSecurityError,
)

from contextlib import contextmanager
from collections.abc import Iterator


@dataclass(frozen=True)
class ExecutionSnapshot:
    root: Path
    filename: str
    sha256: str

    @property
    def source_path(self) -> Path:
        return self.root / self.filename


def create_execution_snapshot(
    workspace: Path,
    filename: str,
) -> ExecutionSnapshot:
    workspace = Path(workspace)

    if workspace.is_symlink():
        raise WorkspaceSecurityError(
            "Workspace symlinks are not permitted"
        )

    root = workspace.resolve(strict=True)

    if not root.is_dir():
        raise WorkspaceSecurityError(
            "Workspace must be a directory"
        )

    relative = Path(filename)

    if (
        not filename
        or "\x00" in filename
        or "\\" in filename
        or relative.is_absolute()
        or ".." in relative.parts
        or "." in relative.parts
    ):
        raise WorkspaceSecurityError(
            "Invalid execution filename"
        )

    current = root
    for part in relative.parts:
        current = current / part

        if current.is_symlink():
            raise WorkspaceSecurityError(
                "Symlinks are not permitted"
            )

    source = current
    source_stat = source.lstat()

    if not stat.S_ISREG(source_stat.st_mode):
        raise WorkspaceSecurityError(
            "Execution source must be a regular file"
        )

    if source_stat.st_size > 1024 * 1024:
        raise WorkspaceSecurityError(
            "Execution source exceeds 1 MiB"
        )

    # Copy only the selected file, not the whole repository.
    # This avoids copying unrelated files or secrets.
    with source.open("rb") as handle:
        content = handle.read(1024 * 1024 + 1)

    if len(content) > 1024 * 1024:
        raise WorkspaceSecurityError(
            "Execution source exceeds 1 MiB"
        )

    digest = hashlib.sha256(content).hexdigest()

    snapshot_root = Path(
        tempfile.mkdtemp(prefix="agent-snapshot-")
    )

    try:
        destination = snapshot_root / relative
        destination.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with destination.open("xb") as handle:
            handle.write(content)

        os.chmod(destination, 0o444)
        os.chmod(snapshot_root, 0o755)

        return ExecutionSnapshot(
            root=snapshot_root,
            filename=filename,
            sha256=digest,
        )

    except Exception:
        import shutil

        shutil.rmtree(snapshot_root, ignore_errors=True)
        raise


@contextmanager
def managed_execution_snapshot(
    workspace: Path,
    filename: str,
) -> Iterator[ExecutionSnapshot]:
    snapshot = create_execution_snapshot(workspace, filename)

    try:
        yield snapshot
    finally:
        import shutil

        shutil.rmtree(snapshot.root)


def verify_snapshot_integrity(
    snapshot: ExecutionSnapshot,
) -> bool:
    try:
        content = snapshot.source_path.read_bytes()
    except OSError:
        return False

    actual_hash = hashlib.sha256(content).hexdigest()
    return actual_hash == snapshot.sha256
