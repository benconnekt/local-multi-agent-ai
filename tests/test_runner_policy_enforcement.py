
from dataclasses import replace

import pytest

from app.tools.sandbox.docker_runner import DockerSandboxRunner
from app.tools.sandbox.policies import get_execution_policy


def test_approved_policy_accepted():
    runner = DockerSandboxRunner(
        get_execution_policy("python")
    )

    assert runner.policy.language == "python"


def test_modified_image_rejected():
    policy = replace(
        get_execution_policy("python"),
        image="python:latest",
    )

    with pytest.raises(ValueError):
        DockerSandboxRunner(policy)


def test_modified_memory_rejected():
    policy = replace(
        get_execution_policy("python"),
        memory_mb=4096,
    )

    with pytest.raises(ValueError):
        DockerSandboxRunner(policy)


def test_modified_timeout_rejected():
    policy = replace(
        get_execution_policy("python"),
        timeout_seconds=300,
    )

    with pytest.raises(ValueError):
        DockerSandboxRunner(policy)
