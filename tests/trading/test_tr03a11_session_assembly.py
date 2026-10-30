"""TR-03A.11 provisional session assembly regression checks."""
from datetime import datetime, timedelta, timezone
import pytest
from app.trading.services.strategy_data_loader import _check_contiguous, DatasetNotReady

UTC = timezone.utc

def candle(t, close=1.1):
    return {'timestamp': t.isoformat(), 'open': 1.1, 'high': 1.2,
            'low': 1.0, 'close': close, 'volume': 10}

def test_weekend_gap_allowed_only_at_session_boundary():
    rows = [candle(datetime(2026, 10, 23, h, tzinfo=UTC)) for h in (19, 20)]
    rows += [candle(datetime(2026, 10, 25, h, tzinfo=UTC)) for h in (21, 22)]
    _check_contiguous(rows, 'H1')

def test_missing_open_market_candle_rejected():
    rows = [candle(datetime(2026, 10, 26, h, tzinfo=UTC)) for h in (10, 12)]
    with pytest.raises(DatasetNotReady, match='missing_expected_candles=1'):
        _check_contiguous(rows, 'H1')

def test_closed_market_candle_rejected():
    rows = [candle(datetime(2026, 10, 23, h, tzinfo=UTC)) for h in (20, 21)]
    with pytest.raises(DatasetNotReady, match='unexpected_session_candles=1'):
        _check_contiguous(rows, 'H1')

def test_invalid_ohlc_rejected():
    row = candle(datetime(2026, 10, 26, 10, tzinfo=UTC))
    row['high'] = 0.9
    with pytest.raises(DatasetNotReady, match='invalid_ohlc=1'):
        _check_contiguous([row], 'H1')

def test_m15_missing_in_session_candle_rejected():
    t = datetime(2026, 10, 26, 10, tzinfo=UTC)
    with pytest.raises(DatasetNotReady, match='missing_expected_candles=1'):
        _check_contiguous([candle(t), candle(t + timedelta(minutes=30))], 'M15')

def test_duplicate_timestamp_rejected():
    row = candle(datetime(2026, 10, 26, 10, tzinfo=UTC))
    with pytest.raises(DatasetNotReady, match='duplicate_timestamps=1'):
        _check_contiguous([row, dict(row)], 'H1')
