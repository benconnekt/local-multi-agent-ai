
import pytest

from app.tools.sandbox.policies import (
    build_execution_command,
    get_execution_policy,
)

from app.tools.sandbox.policies import validate_pinned_image

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


@pytest.mark.parametrize(
    "image",
    [
        "python:3.12-slim",
        "node:24-slim",
        "python:latest",
        "node:24-slim@@sha256:" + "a" * 64,
        "python@sha256:invalid",
        "",
    ],
)
def test_mutable_or_invalid_images_rejected(image):
    with pytest.raises(ValueError):
        validate_pinned_image(image)


def test_python_image_is_pinned():
    policy = get_execution_policy("python")
    validate_pinned_image(policy.image)


def test_node_image_is_pinned():
    policy = get_execution_policy("typescript")
    validate_pinned_image(policy.image)
