from datetime import datetime, timedelta, timezone
from app.trading.strategies.multi_timeframe import StrategyConfig, evaluate

START = datetime(2026, 9, 1, tzinfo=timezone.utc)

def bars(n, minutes, price=1.1, step=0.0001):
    return [dict(timestamp=(START + timedelta(minutes=i * minutes)).isoformat(),
                 open=price + i * step, high=price + i * step + 0.0003,
                 low=price + i * step - 0.0003, close=price + i * step + 0.0001)
            for i in range(n)]

def test_requires_certified_data():
    s = evaluate([], [], [], as_of=START.isoformat(), quality_certified=False)
    assert s.decision == 'NO_TRADE'
    assert 'quality' in s.reason.lower()

def test_rejects_insufficient_history():
    s = evaluate([], [], [], as_of=START.isoformat(), quality_certified=True)
    assert s.decision == 'NO_TRADE'

def test_rejects_future_candle():
    a, b, c = bars(200, 240), bars(60, 60), bars(20, 15)
    s = evaluate(a, b, c, as_of=START.isoformat(), quality_certified=True)
    assert s.decision == 'NO_TRADE'
    assert 'Unclosed' in s.reason

def test_rejects_invalid_ohlc():
    a, b, c = bars(200, 240), bars(60, 60), bars(20, 15)
    a[0]['high'] = 0
    s = evaluate(a, b, c, as_of=(START + timedelta(days=40)).isoformat(), quality_certified=True)
    assert s.decision == 'NO_TRADE'
    assert 'Invalid candle' in s.reason

def test_rejects_stale_data():
    a, b, c = bars(200, 240), bars(60, 60), bars(20, 15)
    s = evaluate(a, b, c, as_of=(START + timedelta(days=40)).isoformat(), quality_certified=True)
    assert s.decision == 'NO_TRADE'
    assert 'Stale' in s.reason

def test_config_enforces_risk_caps():
    import pytest
    with pytest.raises(ValueError):
        StrategyConfig(max_risk_fraction=0.01)
    with pytest.raises(ValueError):
        StrategyConfig(reward_to_risk=1.5)

def test_rejects_naive_time():
    s = evaluate([], [], [], as_of='2026-09-01T00:00:00', quality_certified=True)
    assert s.decision == 'NO_TRADE'
