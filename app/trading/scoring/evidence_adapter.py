"""Conservative bridge from verified factor measurements to opportunity scoring.

Never infers strength from BUY/SELL, a dataset's self-reported quality, or a
missing indicator. Evidence producers must supply independently verified
measurements with provenance; missing factors remain unscored.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from app.trading.scoring.opportunity import FactorEvidence, ScoreResult, WEIGHTS, score_opportunity


@dataclass(frozen=True)
class VerifiedMeasurement:
    strength: float
    explanation: str
    source: str


def build_evidence(measurements: Mapping[str, VerifiedMeasurement]) -> dict[str, FactorEvidence]:
    unknown = set(measurements) - set(WEIGHTS)
    if unknown:
        raise ValueError(f"Unknown factors: {', '.join(sorted(unknown))}")
    return {
        name: FactorEvidence(
            strength=measurement.strength,
            explanation=measurement.explanation,
            source=measurement.source,
        )
        for name, measurement in measurements.items()
    }


def evaluate_scoring(
    measurements: Mapping[str, VerifiedMeasurement],
    *,
    strategy_decision: str,
    quality_certified: bool,
    risk_limits_passed: bool,
) -> dict:
    """Return a JSON-serializable score, with hard gates delegated to scorer."""
    result: ScoreResult = score_opportunity(
        build_evidence(measurements),
        strategy_decision=strategy_decision,
        quality_certified=quality_certified,
        risk_limits_passed=risk_limits_passed,
    )
    return result.to_dict()
