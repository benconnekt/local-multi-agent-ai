import pytest
from app.trading.scoring.opportunity import FactorEvidence, score_opportunity, WEIGHTS


def evidence(value=0.8):
    return {name: FactorEvidence(value, f"Observed {name}", "verified_test_source") for name in WEIGHTS}


def run(items=None, decision="BUY", quality=True, risk=True):
    return score_opportunity(items if items is not None else evidence(), strategy_decision=decision,
                             quality_certified=quality, risk_limits_passed=risk)


def test_weights_and_full_score():
    assert sum(WEIGHTS.values()) == 100
    result = run(evidence(1.0))
    assert result.score == 100
    assert result.rating == "A"
    assert result.eligible and result.decision == "BUY"
    assert sum(f.points for f in result.factors if f.points is not None) == 100


@pytest.mark.parametrize("strength,rating", [(0.85,"A"),(0.70,"B"),(0.55,"C"),(0.54,"D")])
def test_rating_boundaries(strength, rating):
    result = run(evidence(strength))
    assert result.rating == rating


def test_missing_macro_is_unrated_not_imputed():
    items = evidence()
    items["macro_sentiment"] = FactorEvidence(None, "No verified news feed")
    result = run(items)
    assert result.score is None
    assert result.rating == "UNRATED"
    assert not result.complete and not result.eligible
    assert result.decision == "NO_TRADE"
    assert "macro_sentiment" in result.reasons[0]


def test_missing_factor_is_unrated():
    items = evidence()
    del items["price_action"]
    result = run(items)
    assert result.score is None
    assert result.decision == "NO_TRADE"


def test_no_trade_cannot_be_overridden_by_high_score():
    result = run(evidence(1.0), decision="NO_TRADE")
    assert result.score == 100 and result.rating == "A"
    assert not result.eligible and result.decision == "NO_TRADE"


def test_risk_gate_overrides_high_score():
    result = run(evidence(1.0), risk=False)
    assert result.decision == "NO_TRADE" and not result.eligible


def test_quality_gate_overrides_high_score():
    result = run(evidence(1.0), quality=False)
    assert result.decision == "NO_TRADE" and not result.eligible


def test_sell_direction_is_preserved():
    assert run(decision="SELL").decision == "SELL"


@pytest.mark.parametrize("bad", [-0.01, 1.01, float("nan"), float("inf")])
def test_invalid_evidence_rejected(bad):
    with pytest.raises(ValueError):
        FactorEvidence(bad, "Invalid", "source")


def test_scored_evidence_requires_provenance():
    with pytest.raises(ValueError):
        FactorEvidence(0.7, "Observation")


def test_unknown_factor_rejected():
    items = evidence()
    items["magic"] = FactorEvidence(1, "Unknown", "source")
    with pytest.raises(ValueError):
        run(items)


def test_json_serialisable_result():
    import json
    json.dumps(run().to_dict())
