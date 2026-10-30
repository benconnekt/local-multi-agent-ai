from datetime import datetime, timedelta, timezone
import pytest
from app.trading.quality.timeframe_freshness import evaluate_freshness

UTC = timezone.utc

def row(ts):
    return {'timestamp': ts.isoformat()}

def test_missing_history_is_fail_closed():
    result = evaluate_freshness([], [], as_of=datetime(2026, 10, 30, 12, tzinfo=UTC))
    assert result['decision'] == 'NO_TRADE'
    assert result['quality_certified'] is False
    assert 'insufficient_H4_warmup' in result['blocking_reasons']

def test_only_completed_h4_is_counted():
    start = datetime(2026, 10, 29, 8, tzinfo=UTC)
    h1 = [row(start + timedelta(hours=i)) for i in range(5)]
    m15 = [row(start + timedelta(minutes=15*i)) for i in range(20)]
    result = evaluate_freshness(h1, m15, as_of=start + timedelta(hours=5))
    assert result['complete_h4_candles'] == 1
    assert result['certified'] is False

def test_naive_cutoff_rejected():
    with pytest.raises(ValueError, match='timezone-aware'):
        evaluate_freshness([], [], as_of=datetime(2026, 10, 30))
