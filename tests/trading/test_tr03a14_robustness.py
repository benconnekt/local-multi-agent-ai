from datetime import datetime, timedelta, timezone
import pytest
from app.trading.research.robustness import analyse_ledger


def example(n=10):
    start = datetime(2026, 9, 1, tzinfo=timezone.utc)
    return {"decision": "NO_TRADE", "research_only": True,
            "quality_certified": False, "audit_pass": True, "instrument": "EURUSD",
            "ledger": [{"signal_time_utc": (start + timedelta(days=i)).isoformat(),
                        "direction": "LONG" if i % 2 else "SHORT",
                        "outcome": "win" if i % 2 else "loss",
                        "r_multiple": 2.0 if i % 2 else -1.0,
                        "weekend_hold": False} for i in range(n)]}


def test_split_and_metrics():
    result = analyse_ledger(example(), minimum_holdout_resolved=2)
    assert result["split"]["training"]["trades"] == 7
    assert result["split"]["holdout"]["trades"] == 3
    assert result["by_direction"]["LONG"]["wins"] == 5
    assert result["validation_pass"] is False
    assert result["decision"] == "NO_TRADE"


def test_small_sample_is_blocked():
    assert analyse_ledger(example())["sample_sufficient"] is False


def test_reject_unsafe_input():
    value = example()
    value["decision"] = "BUY"
    with pytest.raises(ValueError):
        analyse_ledger(value)


def test_reject_duplicate_timestamp():
    value = example()
    value["ledger"][1]["signal_time_utc"] = value["ledger"][0]["signal_time_utc"]
    with pytest.raises(ValueError):
        analyse_ledger(value)


def test_reject_unresolved_with_realised_r():
    value = example()
    value["ledger"][0]["outcome"] = "unresolved"
    with pytest.raises(ValueError):
        analyse_ledger(value)
