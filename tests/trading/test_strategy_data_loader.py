from datetime import datetime, timedelta, timezone
import pytest
from app.trading.services.strategy_data_loader import _h4_from_h1, _check_contiguous, _merge, DatasetNotReady, assemble


def bar(t, close=1.1, volume=None):
    return {'timestamp': t.isoformat(), 'open': close, 'high': close + .001, 'low': close - .001, 'close': close, 'volume': volume}


def test_h4_aggregation_requires_four_hours():
    start = datetime(2026, 10, 20, tzinfo=timezone.utc)
    rows = [bar(start + timedelta(hours=i)) for i in range(5)]
    out = _h4_from_h1(rows)
    assert len(out) == 1
    assert out[0]['volume'] is None


def test_h4_rejects_incomplete_group():
    start = datetime(2026, 10, 20, tzinfo=timezone.utc)
    assert _h4_from_h1([bar(start), bar(start + timedelta(hours=2))]) == []


def test_gap_rejected():
    start = datetime(2026, 10, 20, tzinfo=timezone.utc)
    with pytest.raises(DatasetNotReady, match='gap'):
        _check_contiguous([bar(start), bar(start + timedelta(hours=2))], 'H1')


def test_overlap_conflict_rejected():
    start = datetime(2026, 10, 20, tzinfo=timezone.utc)
    entries = [{'id': 'a', 'timeframe': 'H1', 'candles': [bar(start)]},
               {'id': 'b', 'timeframe': 'H1', 'candles': [bar(start, 1.2)]}]
    with pytest.raises(DatasetNotReady, match='Conflicting'):
        _merge(entries, 'H1', start + timedelta(hours=1))


def test_unclosed_candle_excluded():
    start = datetime(2026, 10, 20, tzinfo=timezone.utc)
    entries = [{'id': 'a', 'timeframe': 'H1', 'candles': [bar(start), bar(start + timedelta(hours=1))]}]
    rows, _ = _merge(entries, 'H1', start + timedelta(hours=1, minutes=30))
    assert len(rows) == 1


def test_missing_history_fails_closed(tmp_path):
    with pytest.raises(DatasetNotReady, match='No verified'):
        assemble(tmp_path, 'EURUSD')
