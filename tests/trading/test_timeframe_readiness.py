from datetime import datetime, timedelta, timezone
from app.trading.services.timeframe_readiness import inspect_timeframes


def entry(tf, timestamps):
    return {'id': f'data-{tf}', 'timeframe': tf, 'candles': [
        {'timestamp': t.isoformat(), 'open': 1, 'high': 2, 'low': 0.5, 'close': 1.5, 'volume': None}
        for t in timestamps]}


def test_missing_all_is_not_certified():
    result = inspect_timeframes([])
    assert result['H1']['status'] == 'missing'
    assert result['H4']['status'] == 'missing_source'
    assert result['alignment']['certified'] is False


def test_complete_h4_groups_are_counted_without_certification():
    start = datetime(2026, 10, 20, tzinfo=timezone.utc)
    result = inspect_timeframes([entry('H1', [start + timedelta(hours=i) for i in range(8)])])
    assert result['H4']['candle_count'] == 2
    assert result['H4']['incomplete_groups'] == 0
    assert result['H4']['status'] == 'insufficient_history'
    assert result['H4']['certified'] is False


def test_incomplete_h4_bucket_is_excluded():
    start = datetime(2026, 10, 20, tzinfo=timezone.utc)
    result = inspect_timeframes([entry('H1', [start + timedelta(hours=i) for i in range(5)])])
    assert result['H4']['candle_count'] == 1
    assert result['H4']['incomplete_groups'] == 1


def test_disjoint_sources_are_not_aligned():
    start = datetime(2026, 10, 20, tzinfo=timezone.utc)
    result = inspect_timeframes([entry('H1', [start]), entry('M15', [start + timedelta(days=2)])])
    assert result['alignment']['overlapping_coverage'] is False


def test_conflicting_overlap_is_invalid():
    start = datetime(2026, 10, 20, tzinfo=timezone.utc)
    first = entry('H1', [start]); second = entry('H1', [start]); second['id'] = 'second'
    second['candles'][0]['close'] = 1.6
    result = inspect_timeframes([first, second])
    assert result['H1']['status'] == 'invalid'
    assert result['H1']['conflict_count'] == 1
    assert result['H4']['status'] == 'invalid_source'
