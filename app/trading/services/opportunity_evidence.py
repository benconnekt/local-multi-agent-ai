"""Conservative, provenance-aware evidence for the read-only research endpoint.

No technical factor is scored without a validated strategy evaluation. The
current dataset loader intentionally cannot certify FX market sessions.
"""
from __future__ import annotations

from typing import Any

from app.trading.scoring.opportunity import FactorEvidence, score_opportunity


def unavailable_score(reason: str) -> dict[str, Any]:
    """Describe missing evidence without asserting a trading opportunity."""
    if not reason.strip():
        raise ValueError("An unavailability reason is required")
    names = (
        "market_structure", "price_action", "timeframe_alignment",
        "momentum_volatility", "macro_sentiment",
    )
    evidence = {
        name: FactorEvidence(strength=None, explanation=reason, source=None)
        for name in names
    }
    return score_opportunity(
        evidence, strategy_decision="NO_TRADE",
        quality_certified=False, risk_limits_passed=False,
    ).to_dict()
