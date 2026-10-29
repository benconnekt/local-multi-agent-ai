
import pytest

from app.tools.sandbox.policies import (
    get_execution_policy,
    validate_execution_command,
)


def test_approved_python_command():
    validate_execution_command(
        get_execution_policy("python"),
        ["python", "-B", "hello.py"],
    )


def test_approved_node_command():
    validate_execution_command(
        get_execution_policy("typescript"),
        ["node", "dist/hello.js"],
    )


@pytest.mark.parametrize(
    "command",
    [
        ["sh", "-c", "echo hello"],
        ["python", "-c", "print('hello')"],
        ["python", "-B", "../outside.py"],
        ["python", "-B", "/etc/passwd"],
        ["python", "-B", "script.sh"],
        ["python", "-B", "hello.py", "--extra"],
        ["python", "-B", "-c"],
    ],
)
def test_unapproved_python_commands(command):
    with pytest.raises(ValueError):
        validate_execution_command(
            get_execution_policy("python"),
            command,
        )


@pytest.mark.parametrize(
    "command",
    [
        ["bash", "script.js"],
        ["node", "../outside.js"],
        ["node", "--eval"],
        ["node", "script.ts"],
        ["node", "script.js", "--inspect"],
    ],
)
def test_unapproved_node_commands(command):
    with pytest.raises(ValueError):
        validate_execution_command(
            get_execution_policy("typescript"),
            command,
        )
