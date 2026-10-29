
import shutil
import subprocess

import pytest


@pytest.fixture
def docker_available():
    if shutil.which("docker") is None:
        pytest.skip("Docker CLI is not installed")

    try:
        result = subprocess.run(
            ["docker", "info", "--format", "{{.ServerVersion}}"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        pytest.skip("Docker daemon is unavailable")

    if result.returncode != 0:
        pytest.skip("Docker daemon is unavailable")
