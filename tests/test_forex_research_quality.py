from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from app.trading.agents import historical_evidence as he
from app.trading.agents.market_analyst import market_data


def test_historical_market_data_available_but_uncertified(monkeypatch):
    t = datetime(2025, 1, 1, tzinfo=timezone.utc)
    candles = [SimpleNamespace(timestamp=t+timedelta(hours=i), close=1.1+i/10000,
               high=1.11+i/10000, low=1.09+i/10000) for i in range(40)]
    monkeypatch.setattr(he, 'discover', lambda _: [{
        'instrument': 'EURUSD', 'source': 'oanda_v20', 'timeframe': 'H1',
        'data_kind': 'historical_real', 'last_timestamp': candles[-1].timestamp.isoformat(),
        'id': 'oanda_v20:test', 'candles': candles, 'quality_status': 'imported_uncertified'}])
    context = he.build_historical_evidence('EURUSD')
    finding = market_data({'verified_context': context['verified_context']})['findings']['market_data']
    assert finding['status'] == 'available_uncertified'
    assert finding['quality_certified'] is False
    assert finding['not_live'] is True
    evidence = context['verified_context']['technical']
    assert evidence['indicator_coverage']['sma_20_observed'] == 20
    assert 'RSI' in evidence['missing_indicators']
    assert 'last_close_minus_sma_20' in evidence


def test_no_evidence_still_unavailable():
    finding = market_data({'verified_context': {}, 'candles': []})['findings']['market_data']
    assert finding['status'] == 'unavailable'
