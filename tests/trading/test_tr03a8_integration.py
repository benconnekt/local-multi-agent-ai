"""Focused regression checks for fail-closed OANDA catalogue integration."""
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from app.trading.data.catalogue import _locations
from app.trading.services.strategy_data_loader import DatasetNotReady, _merge, _h4_from_h1, assemble


def test_sibling_catalogue_locations():
    locations = _locations(Path('/repo/data/forex/historical_real'))
    assert locations == [Path('/repo/data/forex/historical_real'), Path('/repo/data/forex/historical_oanda')]


def test_overlapping_identical_candles_deduplicated():
    ts = datetime(2026, 10, 1, tzinfo=timezone.utc)
    candle = {'timestamp': ts.isoformat(), 'open': 1.1, 'high': 1.2, 'low': 1.0, 'close': 1.15, 'volume': 10}
    entries = [{'id': 'small', 'timeframe': 'H1', 'candles': [candle]}, {'id': 'large', 'timeframe': 'H1', 'candles': [candle]}]
    rows, ids = _merge(entries, 'H1', ts + timedelta(hours=2))
    assert len(rows) == 1
    assert ids == ['small', 'large']


def test_conflicting_overlapping_candles_rejected():
    ts = datetime(2026, 10, 1, tzinfo=timezone.utc)
    candle = {'timestamp': ts.isoformat(), 'open': 1.1, 'high': 1.2, 'low': 1.0, 'close': 1.15, 'volume': 10}
    entries = [{'id': 'a', 'timeframe': 'H1', 'candles': [candle]}, {'id': 'b', 'timeframe': 'H1', 'candles': [{**candle, 'close': 1.16}]}]
    with pytest.raises(DatasetNotReady, match='Conflicting overlapping'):
        _merge(entries, 'H1', ts + timedelta(hours=2))


def test_h4_requires_four_aligned_h1_bars():
    ts = datetime(2026, 10, 1, tzinfo=timezone.utc)
    rows = [{'timestamp': (ts + timedelta(hours=i)).isoformat(), 'open': 1.0, 'high': 2.0, 'low': 0.5, 'close': 1.5, 'volume': 1.0} for i in range(4)]
    assert len(_h4_from_h1(rows)) == 1
    assert _h4_from_h1(rows[:3]) == []


def test_provider_mixing_rejected(monkeypatch, tmp_path):
    from app.trading.services import strategy_data_loader as loader
    monkeypatch.setattr(loader, 'discover', lambda _: [
        {'instrument': 'EURUSD', 'data_kind': 'historical_real', 'source': 'oanda_v20'},
        {'instrument': 'EURUSD', 'data_kind': 'historical_real', 'source': 'yahoo_finance'},
    ])
    with pytest.raises(DatasetNotReady, match='Multiple historical providers'):
        assemble(tmp_path, 'EURUSD')
