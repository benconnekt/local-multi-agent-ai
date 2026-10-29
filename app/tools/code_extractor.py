
import re


FENCED_CODE = re.compile(
    r"```(?P<language>[a-zA-Z0-9+#.-]*)[ \t]*\r?\n"
    r"(?P<code>.*?)"
    r"\r?\n?```",
    flags=re.DOTALL,
)

LANGUAGE_ALIASES = {
    "py": "python",
    "python": "python",
    "ts": "typescript",
    "tsx": "typescript",
    "typescript": "typescript",
    "js": "javascript",
    "jsx": "javascript",
    "javascript": "javascript",
    "dart": "dart",
    "java": "java",
}


def normalize_language(language: str) -> str:
    value = language.strip().lower()
    return LANGUAGE_ALIASES.get(value, value)


def extract_code(response: str, language: str) -> str:
    expected = normalize_language(language)

    matches = list(FENCED_CODE.finditer(response))

    if matches:
        for match in matches:
            detected = normalize_language(
                match.group("language")
            )

            if detected == expected:
                return match.group("code").strip()

        # Accept an unlabelled code fence.
        for match in matches:
            if not match.group("language"):
                return match.group("code").strip()

        raise ValueError(
            f"No {expected} code block found in response."
        )

    return response.strip()


# Preserve compatibility with the original Python service.
def extract_python_code(response: str) -> str:
    return extract_code(response, "python")
