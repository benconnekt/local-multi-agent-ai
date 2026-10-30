"""Fail-closed research risk assessment."""

def risk_review(state: dict) -> dict:
    return {"findings": {"risk": {
        "status": "blocked",
        "summary": "No independent certification; execution and research-signal eligibility disabled",
    }}}
