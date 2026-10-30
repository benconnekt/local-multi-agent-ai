from app.trading.services.opportunity_evidence import unavailable_score


def test_uncertified_market_is_unrated_and_fail_closed():
    result = unavailable_score("FX session calendar certification pending")
    assert result["score"] is None
    assert result["rating"] == "UNRATED"
    assert result["complete"] is False
    assert result["eligible"] is False
    assert result["decision"] == "NO_TRADE"
    assert len(result["factors"]) == 5
    assert all(not factor["available"] for factor in result["factors"])
    assert all(factor["points"] is None for factor in result["factors"])


def test_unavailability_requires_reason():
    import pytest
    with pytest.raises(ValueError):
        unavailable_score("  ")
