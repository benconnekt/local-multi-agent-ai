
import pytest

from app.tools.code_extractor import (
    extract_code,
    normalize_language,
)


def test_extract_python_code():
    response = """```python
def add(a, b):
    return a + b
```"""

    assert extract_code(response, "python") == (
        "def add(a, b):\n    return a + b"
    )


def test_extract_typescript_code():
    response = """```typescript
function isEven(value: number): boolean {
    return value % 2 === 0;
}
```"""

    code = extract_code(response, "typescript")

    assert "function isEven" in code


def test_extract_alias():
    response = """```ts
const value: number = 42;
```"""

    assert extract_code(response, "typescript") == (
        "const value: number = 42;"
    )


def test_extract_unlabelled_code():
    response = """```
print("Hello")
```"""

    assert extract_code(response, "python") == (
        'print("Hello")'
    )


def test_reject_wrong_language():
    response = """```javascript
console.log("Hello");
```"""

    with pytest.raises(ValueError):
        extract_code(response, "python")


def test_normalize_language():
    assert normalize_language("TS") == "typescript"
    assert normalize_language("PY") == "python"
    assert normalize_language("DART") == "dart"
