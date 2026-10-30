from datetime import datetime, timedelta, timezone
import pytest
from app.trading.quality.validation import validate_candles, aggregate_h1_to_h4, filter_date_range

UTC = timezone.utc

def candles(start, count, minutes=60):
    return [{"timestamp": (start + timedelta(minutes=minutes*i)).isoformat(), "open": 1.1, "high": 1.2, "low": 1.0, "close": 1.15, "volume": None} for i in range(count)]

def test_complete_day():
    start = datetime(2026, 10, 20, tzinfo=UTC)
    report = validate_candles(candles(start, 24), "H1", start, start + timedelta(days=1))
    assert report.research_ready and report.expected == 24

def test_missing_candle():
    start = datetime(2026, 10, 20, tzinfo=UTC)
    report = validate_candles(candles(start, 24)[:-1], "H1", start, start + timedelta(days=1))
    assert report.status == "failed" and len(report.missing) == 1

def test_weekend_not_counted():
    start = datetime(2026, 10, 24, tzinfo=UTC)  # Saturday
    report = validate_candles([], "H1", start, start + timedelta(days=1))
    assert report.expected == 0 and report.research_ready

def test_h4_aggregation():
    start = datetime(2026, 10, 20, tzinfo=UTC)
    result = aggregate_h1_to_h4(candles(start, 8))
    assert len(result) == 2 and result[0]["open"] == 1.1

def test_h4_partial_rejected():
    start = datetime(2026, 10, 20, tzinfo=UTC)
    with pytest.raises(ValueError, match="Incomplete"):
        aggregate_h1_to_h4(candles(start, 3))

def test_date_filter():
    start = datetime(2026, 10, 20, tzinfo=UTC)
    result = filter_date_range(candles(start, 5), start + timedelta(hours=1), start + timedelta(hours=3))
    assert len(result) == 2

def test_h4_aggregation_accepts_empty_forex_volume():
    from datetime import datetime, timedelta, timezone
    from app.trading.quality.validation import aggregate_h1_to_h4

    start = datetime(2026, 10, 20, tzinfo=timezone.utc)

    candles = [
        {
            "timestamp": (
                start + timedelta(hours=i)
            ).isoformat(),
            "open": "1.1000",
            "high": "1.1020",
            "low": "1.0990",
            "close": "1.1010",
            "volume": "",
        }
        for i in range(4)
    ]

    result = aggregate_h1_to_h4(candles)

    assert len(result) == 1
    assert result[0]["volume"] is None