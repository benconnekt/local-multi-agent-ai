from datetime import datetime, timedelta, timezone
from app.trading.quality.h4_integrity import analyse_h4, closed_timeframe_alignment

UTC = timezone.utc

def rows(start, count, minutes):
    return [{'timestamp': (start + timedelta(minutes=minutes * i)).isoformat()} for i in range(count)]

def test_complete_h4_bucket():
    result = analyse_h4(rows(datetime(2026, 10, 20, tzinfo=UTC), 4, 60))
    assert result['complete_candles'] == 1
    assert result['incomplete_groups'] == 0
    assert not result['independently_certified']

def test_missing_in_session_h1_hour():
    data = rows(datetime(2026, 10, 20, tzinfo=UTC), 4, 60)
    result = analyse_h4([data[0], data[1], data[3]])
    assert result['incomplete_reasons']['missing_in_session'] == 1
    assert result['status'] == 'invalid_source'

def test_weekend_boundary_is_not_a_fabricated_h4():
    data = rows(datetime(2026, 10, 23, 19, tzinfo=UTC), 2, 60)
    result = analyse_h4(data)
    assert result['complete_candles'] == 0
    assert result['incomplete_groups'] == 2

def test_no_lookahead_at_cutoff():
    start = datetime(2026, 10, 20, tzinfo=UTC)
    result = closed_timeframe_alignment(rows(start, 5, 60), rows(start, 20, 15),
                                        as_of=start + timedelta(hours=3))
    assert result['h4_complete_candles'] == 0
    assert not result['certified']
    assert not result['research_signal_eligible']

def test_naive_timestamp_rejected():
    import pytest
    with pytest.raises(ValueError, match='timezone-aware'):
        analyse_h4([{'timestamp': '2026-10-20T00:00:00'}])
