import pytest
from app.trading.scoring.evidence_adapter import VerifiedMeasurement, build_evidence, evaluate_scoring


def test_missing_macro_is_unrated_and_never_eligible():
    measurements = {
        name: VerifiedMeasurement(0.8, f"Verified {name}", "validated:test")
        for name in ("market_structure", "price_action", "timeframe_alignment", "momentum_volatility")
    }
    result = evaluate_scoring(measurements, strategy_decision="BUY", quality_certified=True, risk_limits_passed=True)
    assert result["score"] is None
    assert result["rating"] == "UNRATED"
    assert result["decision"] == "NO_TRADE"
    assert "macro_sentiment" in result["reasons"][0]


def test_empty_evidence_stays_unrated():
    result = evaluate_scoring({}, strategy_decision="NO_TRADE", quality_certified=False, risk_limits_passed=False)
    assert result["score"] is None
    assert len(result["factors"]) == 5
    assert not result["eligible"]


def test_invalid_factor_rejected():
    with pytest.raises(ValueError, match="Unknown factors"):
        build_evidence({"imaginary": VerifiedMeasurement(0.5, "test", "test")})


def test_scoring_cannot_override_strategy_no_trade():
    names = ("market_structure", "price_action", "timeframe_alignment", "momentum_volatility", "macro_sentiment")
    measurements = {name: VerifiedMeasurement(1.0, "Verified", "validated:test") for name in names}
    result = evaluate_scoring(measurements, strategy_decision="NO_TRADE", quality_certified=True, risk_limits_passed=True)
    assert result["score"] == 100
    assert result["rating"] == "A"
    assert result["decision"] == "NO_TRADE"
