from datetime import datetime, timedelta, timezone
from app.trading.quality.fx_session_validation import audit_sessions
from app.trading.quality.holiday_calendar import OANDA_OBSERVED_2025_2026_V1 as calendar

UTC = timezone.utc

def row(t):
    return {'timestamp': t, 'open': 1.1, 'high': 1.2, 'low': 1.0, 'close': 1.1}

def test_christmas_gap_only_with_explicit_calendar():
    start = datetime(2025, 12, 24, 20, tzinfo=UTC)
    end = datetime(2025, 12, 26, 1, tzinfo=UTC)
    bars = [row(t) for i in range(int((end-start)/timedelta(hours=1))+1)
            if not calendar.is_closed(t := start + i*timedelta(hours=1))]
    assert audit_sessions(bars, 'H1').missing_expected_candles == 24
    result = audit_sessions(bars, 'H1', calendar=calendar)
    assert result.provisional_schedule_pass
    assert result.excluded_calendar_intervals == 24
    assert not result.calendar_verified
    assert not result.independently_certified

def test_unknown_gap_still_fails():
    start = datetime(2026, 10, 20, tzinfo=UTC)
    bars = [row(start + i*timedelta(hours=1)) for i in (0, 1, 3)]
    assert not audit_sessions(bars, 'H1', calendar=calendar).provisional_schedule_pass

def test_unexpected_candle_during_closure_fails():
    bars = [row(datetime(2025, 12, 25, 12, tzinfo=UTC))]
    result = audit_sessions(bars, 'H1', calendar=calendar)
    assert result.unexpected_session_candles == 1
    assert not result.provisional_schedule_pass

def test_m15_new_year_gap():
    start = datetime(2025, 12, 31, 21, tzinfo=UTC)
    end = datetime(2026, 1, 1, 23, tzinfo=UTC)
    bars = [row(t) for i in range(int((end-start)/timedelta(minutes=15))+1)
            if not calendar.is_closed(t := start + i*timedelta(minutes=15))]
    result = audit_sessions(bars, 'M15', calendar=calendar)
    assert result.excluded_calendar_intervals == 96
    assert result.provisional_schedule_pass
