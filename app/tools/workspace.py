
from pathlib import Path
from tempfile import TemporaryDirectory


class AgentWorkspace:
    def __init__(self):
        self._temporary_directory = TemporaryDirectory(
            prefix="agent-studio-"
        )
        self.root = Path(self._temporary_directory.name).resolve()

    def write_file(self, filename: str, content: str) -> Path:
        if not filename or Path(filename).is_absolute():
            raise ValueError("A relative filename is required")

        destination = (self.root / filename).resolve()

        if not destination.is_relative_to(self.root):
            raise ValueError("Path escapes the agent workspace")

        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(content, encoding="utf-8")

        return destination

    def read_file(self, filename: str) -> str:
        destination = (self.root / filename).resolve()

        if not destination.is_relative_to(self.root):
            raise ValueError("Path escapes the agent workspace")

        return destination.read_text(encoding="utf-8")

    def close(self):
        self._temporary_directory.cleanup()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
