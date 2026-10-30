from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch
import pytest
from app.trading.research.historical_runner import run_historical_backtest, _continuous
from app.trading.research.backtest import Bar

UTC = timezone.utc


def test_rejects_unsupported_provider():
    with pytest.raises(ValueError, match='provider'):
        run_historical_backtest(Path('/tmp/unused'), 'EURUSD', provider='unknown')


def test_rejects_unsupported_instrument():
    with pytest.raises(ValueError, match='instrument'):
        run_historical_backtest(Path('/tmp/unused'), 'BTCUSD')


def test_rejects_missing_data():
    with patch('app.trading.research.historical_runner.discover', return_value=[]):
        with pytest.raises(ValueError, match='No historical data'):
            run_historical_backtest(Path('/tmp/unused'), 'EURUSD')


def test_breakout_requires_four_contiguous_candles():
    from datetime import timedelta
    t = datetime(2026, 10, 29, 10, tzinfo=UTC)
    bars = [Bar(t + timedelta(minutes=15*i), 1, 2, .5, 1.5) for i in (0, 1, 3, 4)]
    assert not _continuous(bars, t + timedelta(minutes=75), timedelta(minutes=15), 4)


def test_safety_base_is_fail_closed():
    from app.trading.research.historical_runner import BASE
    assert BASE['decision'] == 'NO_TRADE'
    assert BASE['research_only'] is True
    assert BASE['quality_certified'] is False
    assert BASE['research_signal_eligible'] is False
