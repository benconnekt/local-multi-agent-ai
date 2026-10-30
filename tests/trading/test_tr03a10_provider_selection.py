"""TR-03A.10 provider isolation and fail-closed regression checks."""
from datetime import datetime, timezone
from pathlib import Path
import pytest
from app.trading.services import strategy_data_loader as loader
from app.trading.services.timeframe_readiness import inspect_timeframes
from app.api.routes import trading_strategy as route


def _entry(source, timeframe='H1', close=1.15):
    return {'id': f'{source}:{timeframe}', 'instrument': 'EURUSD',
            'data_kind': 'historical_real', 'source': source,
            'timeframe': timeframe, 'quality_status': 'imported_uncertified',
            'count': 1, 'last_timestamp': '2026-10-26T12:00:00+00:00',
            'candles': [{'timestamp': '2026-10-26T12:00:00+00:00',
                         'open': 1.1, 'high': 1.2, 'low': 1.0,
                         'close': close, 'volume': 10}]}


def test_loader_requires_provider_with_multiple_sources(monkeypatch):
    monkeypatch.setattr(loader, 'discover', lambda _: [_entry('oanda_v20'), _entry('yahoo_finance')])
    with pytest.raises(loader.DatasetNotReady, match='explicit provider selection'):
        loader.assemble(Path('.'), 'EURUSD')


def test_loader_selected_provider_does_not_merge_other_source(monkeypatch):
    monkeypatch.setattr(loader, 'discover', lambda _: [_entry('oanda_v20'), _entry('yahoo_finance', close=1.16)])
    with pytest.raises(loader.DatasetNotReady) as exc:
        loader.assemble(Path('.'), 'EURUSD', provider='oanda_v20',
                        as_of=datetime(2026, 10, 27, tzinfo=timezone.utc))
    assert 'Conflicting overlapping' not in str(exc.value)
    assert 'Missing M15' in str(exc.value)


def test_timeframes_mixed_sources_fail_closed():
    result = inspect_timeframes([_entry('oanda_v20'), _entry('yahoo_finance')])
    assert result['status'] == 'provider_selection_required'
    assert result['H1'] is None


def test_timeframes_selected_provider_only():
    result = inspect_timeframes([_entry('oanda_v20'), _entry('yahoo_finance', close=1.16)], provider='oanda_v20')
    assert result['H1']['candle_count'] == 1
    assert result['H1']['conflict_count'] == 0
    assert result['provider'] == 'oanda_v20'


def test_api_selection_and_safety(monkeypatch):
    monkeypatch.setattr(route, 'discover', lambda _: [_entry('oanda_v20'), _entry('yahoo_finance', close=1.16)])
    response = route.analyse(instrument='EURUSD', provider='oanda_v20')
    assert response['provider'] == 'oanda_v20'
    assert response['available_providers'] == ['oanda_v20', 'yahoo_finance']
    assert response['decision'] == 'NO_TRADE'
    assert response['quality_certified'] is False
    assert response['research_only'] is True
    assert all(item['source'] == 'oanda_v20' for item in response['datasets'].values())
    assert response['timeframe_readiness']['provider'] == 'oanda_v20'
    assert response['session_readiness']['provider'] == 'oanda_v20'


def test_api_ambiguous_sources_fail_closed(monkeypatch):
    monkeypatch.setattr(route, 'discover', lambda _: [_entry('oanda_v20'), _entry('yahoo_finance')])
    response = route.analyse(instrument='EURUSD', provider=None)
    assert response['provider'] is None
    assert response['decision'] == 'NO_TRADE'
    assert response['timeframe_readiness']['status'] == 'provider_selection_required'
    assert response['session_readiness']['status'] == 'provider_selection_required'
