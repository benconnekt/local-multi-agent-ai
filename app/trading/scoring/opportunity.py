"""Explainable confluence scoring; never authorises a trading signal.

Scores are heuristic research descriptors, not calibrated probabilities.
Missing evidence stays missing and never receives a default score.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from math import isfinite
from typing import Literal, Mapping

FactorName = Literal[
    "market_structure", "price_action", "timeframe_alignment",
    "momentum_volatility", "macro_sentiment",
]
Rating = Literal["A", "B", "C", "D", "UNRATED"]
Decision = Literal["BUY", "SELL", "NO_TRADE"]

WEIGHTS: dict[str, int] = {
    "market_structure": 25,
    "price_action": 25,
    "timeframe_alignment": 20,
    "momentum_volatility": 15,
    "macro_sentiment": 15,
}

@dataclass(frozen=True)
class FactorEvidence:
    # Strength of evidence for a proposed setup, not probability of success.
    strength: float | None
    explanation: str
    source: str | None = None

    def __post_init__(self) -> None:
        if self.strength is not None:
            if not isfinite(self.strength) or not 0 <= self.strength <= 1:
                raise ValueError("Factor strength must be finite and between 0 and 1")
        if not self.explanation.strip():
            raise ValueError("Every factor requires an explanation")
        if self.strength is not None and not (self.source and self.source.strip()):
            raise ValueError("Scored evidence must have a source")

@dataclass(frozen=True)
class FactorResult:
    name: str
    weight: int
    points: float | None
    available: bool
    explanation: str
    source: str | None

@dataclass(frozen=True)
class ScoreResult:
    score: float | None
    rating: Rating
    complete: bool
    eligible: bool
    decision: Decision
    reasons: tuple[str, ...]
    factors: tuple[FactorResult, ...]
    scoring_version: str = "tr03a3-v1"
    probability_calibrated: bool = False
    research_only: bool = True

    def to_dict(self) -> dict:
        return asdict(self)


def score_opportunity(
    evidence: Mapping[str, FactorEvidence],
    *,
    strategy_decision: Decision,
    quality_certified: bool,
    risk_limits_passed: bool,
) -> ScoreResult:
    """Score documented evidence; hard gates always take precedence.

    All five factors must be present to publish a numeric score. An
    incomplete score is UNRATED; it must not be presented as 0 or a percent.
    """
    if strategy_decision not in ("BUY", "SELL", "NO_TRADE"):
        raise ValueError("Unknown strategy decision")
    unexpected = set(evidence) - set(WEIGHTS)
    if unexpected:
        raise ValueError(f"Unknown scoring factors: {', '.join(sorted(unexpected))}")
    if any(not isinstance(v, FactorEvidence) for v in evidence.values()):
        raise TypeError("Evidence values must be FactorEvidence")

    factors: list[FactorResult] = []
    missing: list[str] = []
    total = 0.0
    for name, weight in WEIGHTS.items():
        item = evidence.get(name)
        available = item is not None and item.strength is not None
        if not available:
            missing.append(name)
        points = round(weight * item.strength, 4) if available and item is not None else None
        if points is not None:
            total += points
        factors.append(FactorResult(
            name=name, weight=weight, points=points, available=available,
            explanation=item.explanation if item is not None else "Evidence unavailable",
            source=item.source if item is not None else None,
        ))

    complete = not missing
    score = round(total, 2) if complete else None
    rating: Rating = "UNRATED"
    if score is not None:
        rating = "A" if score >= 85 else "B" if score >= 70 else "C" if score >= 55 else "D"

    reasons: list[str] = []
    if missing:
        reasons.append("Missing evidence: " + ", ".join(missing))
    if not quality_certified:
        reasons.append("Historical data quality is not certified")
    if not risk_limits_passed:
        reasons.append("Risk limits failed or have not been verified")
    if strategy_decision == "NO_TRADE":
        reasons.append("Underlying deterministic strategy returned NO_TRADE")
    eligible = complete and quality_certified and risk_limits_passed and strategy_decision != "NO_TRADE"
    # Scoring never changes the strategy's direction. Ineligible = NO_TRADE.
    decision: Decision = strategy_decision if eligible else "NO_TRADE"
    return ScoreResult(score, rating, complete, eligible, decision,
                       tuple(reasons), tuple(factors))
