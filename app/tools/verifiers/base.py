
from dataclasses import dataclass
from typing import Literal, Protocol


VerificationStatus = Literal[
    "passed",
    "failed",
    "unsupported",
]


@dataclass(frozen=True)
class VerificationResult:
    language: str
    status: VerificationStatus
    message: str

    @property
    def passed(self) -> bool:
        return self.status == "passed"


class CodeVerifier(Protocol):
    def verify(self, source: str) -> VerificationResult:
        ...
