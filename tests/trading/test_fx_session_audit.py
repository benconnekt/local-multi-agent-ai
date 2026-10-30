from datetime import datetime, timedelta, timezone
import pytest
from app.trading.quality.fx_session_audit import audit_candles


def bars(start, count, minutes):
    return [{'timestamp': (start + timedelta(minutes=minutes*i)).isoformat()} for i in range(count)]


def test_contiguous_weekday():
    result = audit_candles(bars(datetime(2026, 10, 20, tzinfo=timezone.utc), 24, 60), 'H1')
    assert result.missing == result.unexpected == result.duplicate == 0
    assert result.certified is False


def test_weekend_gap_not_missing_under_assumption():
    fri = bars(datetime(2026, 10, 23, 20, tzinfo=timezone.utc), 2, 60)
    sun = bars(datetime(2026, 10, 25, 22, tzinfo=timezone.utc), 2, 60)
    result = audit_candles(fri + sun, 'H1')
    assert result.missing == 0
    assert result.certified is False


def test_missing_weekday_candle():
    candles = bars(datetime(2026, 10, 20, tzinfo=timezone.utc), 5, 15)
    result = audit_candles(candles[:2] + candles[3:], 'M15')
    assert result.missing == 1


def test_duplicate_detected():
    candles = bars(datetime(2026, 10, 20, tzinfo=timezone.utc), 2, 60)
    result = audit_candles(candles + [candles[0]], 'H1')
    assert result.duplicate == 1


def test_unexpected_weekend_candle():
    candles = bars(datetime(2026, 10, 24, tzinfo=timezone.utc), 2, 60)
    result = audit_candles(candles, 'H1')
    assert result.unexpected == 2


def test_naive_rejected():
    with pytest.raises(ValueError):
        audit_candles([{'timestamp': '2026-10-20T00:00:00'}], 'H1')


def test_unaligned_rejected():
    with pytest.raises(ValueError):
        audit_candles([{'timestamp': '2026-10-20T00:05:00+00:00'}], 'M15')


def test_empty_rejected():
    with pytest.raises(ValueError):
        audit_candles([], 'H1')
