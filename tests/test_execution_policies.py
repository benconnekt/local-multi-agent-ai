
import pytest

from app.tools.sandbox.policies import (
    build_execution_command,
    get_execution_policy,
)


def test_python_policy():
    policy = get_execution_policy("python")

    assert policy.executable == "python"
    assert policy.memory_mb == 256


def test_typescript_alias():
    policy = get_execution_policy("ts")

    assert policy.language == "typescript"


def test_python_command():
    command = build_execution_command(
        "python",
        "generated.py",
    )

    assert command == [
        "python",
        "-B",
        "generated.py",
    ]


def test_typescript_command():
    command = build_execution_command(
        "typescript",
        "dist/generated.js",
    )

    assert command == [
        "node",
        "dist/generated.js",
    ]


@pytest.mark.parametrize(
    "filename",
    [
        "../secret.py",
        "/etc/passwd",
        "folder/../../secret.py",
        "script.sh",
        "folder\\script.py",
        "",
    ],
)
def test_invalid_python_paths(filename):
    with pytest.raises(ValueError):
        build_execution_command("python", filename)


def test_unknown_language_rejected():
    with pytest.raises(ValueError):
        get_execution_policy("ruby")


def test_python_rejects_javascript():
    with pytest.raises(ValueError):
        build_execution_command("python", "script.js")
