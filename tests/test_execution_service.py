
import pytest

from app.tools.sandbox.execution_service import (
    SandboxExecutionService,
)
from app.tools.workspace import AgentWorkspace

from conftest import docker_available;


def test_python_execution():
    service = SandboxExecutionService()

    with AgentWorkspace() as workspace:
        workspace.write_file(
            "hello.py",
            "print('Hello from James')",
        )

        result = service.execute(
            language="python",
            workspace=workspace.root,
            filename="hello.py",
        )

        assert result.passed, result.stderr
        assert "Hello from James" in result.stdout


def test_typescript_compiled_javascript_execution(docker_available):
    service = SandboxExecutionService()

    with AgentWorkspace() as workspace:
        workspace.write_file(
            "dist/hello.js",
            "console.log('Hello from Node 24')",
        )

        result = service.execute(
            language="typescript",
            workspace=workspace.root,
            filename="dist/hello.js",
        )

        assert result.passed, result.stderr
        assert "Hello from Node 24" in result.stdout


def test_unsupported_language_rejected():
    service = SandboxExecutionService()

    with AgentWorkspace() as workspace:
        with pytest.raises(ValueError):
            service.execute(
                language="ruby",
                workspace=workspace.root,
                filename="script.rb",
            )


def test_path_traversal_rejected():
    service = SandboxExecutionService()

    with AgentWorkspace() as workspace:
        with pytest.raises(ValueError):
            service.execute(
                language="python",
                workspace=workspace.root,
                filename="../outside.py",
            )
