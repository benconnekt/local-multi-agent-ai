
from app.services.code_verification import verify_generated_code
from app.tools.workspace import AgentWorkspace


def test_valid_generated_code_is_saved():
    response = """```python
def add(a, b):
    return a + b
```"""

    with AgentWorkspace() as workspace:
        result = verify_generated_code(response, workspace)

        assert result.passed
        assert workspace.read_file("generated.py") == (
            "def add(a, b):\n    return a + b"
        )


def test_invalid_code_is_not_saved():
    response = """```python
def add(a, b)
    return a + b
```"""

    with AgentWorkspace() as workspace:
        result = verify_generated_code(response, workspace)

        assert not result.passed
        assert not (workspace.root / "generated.py").exists()
