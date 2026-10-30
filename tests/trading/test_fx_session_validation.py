from datetime import datetime, timedelta, timezone
from app.trading.quality.fx_session_validation import audit_sessions, derive_h4_summary

UTC = timezone.utc

def bars(start, count, step_minutes):
    return [{'timestamp': start + timedelta(minutes=i*step_minutes), 'open': 1.1, 'high': 1.2, 'low': 1.0, 'close': 1.15} for i in range(count)]

def test_contiguous_midweek_h1():
    result = audit_sessions(bars(datetime(2026, 10, 20, tzinfo=UTC), 24, 60), 'H1')
    assert result.provisional_schedule_pass
    assert not result.independently_certified

def test_detects_missing_midweek_bar():
    data = bars(datetime(2026, 10, 20, tzinfo=UTC), 4, 60)
    result = audit_sessions(data[:2] + data[3:], 'H1')
    assert result.missing_expected_candles == 1

def test_weekend_gap_expected():
    data = bars(datetime(2026, 10, 23, 19, tzinfo=UTC), 2, 60)
    data += bars(datetime(2026, 10, 25, 21, tzinfo=UTC), 2, 60)

    result = audit_sessions(data, 'H1')

    assert result.provisional_schedule_pass
    assert result.missing_expected_candles == 0
    assert result.unexpected_session_candles == 0

def test_weekend_candle_flagged():
    result = audit_sessions(bars(datetime(2026, 10, 24, 12, tzinfo=UTC), 1, 60), 'H1')
    assert result.unexpected_session_candles == 1

def test_duplicate_and_invalid_ohlc():
    data = bars(datetime(2026, 10, 20, tzinfo=UTC), 2, 60)
    bad = dict(data[0], high=0.5)
    result = audit_sessions(data + [bad], 'H1')
    assert result.duplicate_timestamps == 1
    assert result.invalid_ohlc == 1

def test_misaligned_m15():
    result = audit_sessions(bars(datetime(2026, 10, 20, 0, 5, tzinfo=UTC), 2, 15), 'M15')
    assert result.misaligned_timestamps == 2

def test_h4_complete_groups():
    result = derive_h4_summary(bars(datetime(2026, 10, 20, tzinfo=UTC), 9, 60), minimum_h4=2)
    assert result['complete_candles'] == 2
    assert result['incomplete_groups'] == 1
    assert result['history_sufficient']
    assert not result['independently_certified']

def test_empty_fails_closed():
    result = audit_sessions([], 'H1')
    assert not result.provisional_schedule_pass
