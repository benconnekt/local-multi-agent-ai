from types import SimpleNamespace
import pytest
from app.trading.agents import historical_evidence as module


def test_historical_evidence_grounded(monkeypatch):
    from datetime import datetime, timedelta, timezone
    t = datetime(2025, 1, 1, tzinfo=timezone.utc)
    candles = [SimpleNamespace(timestamp=t+timedelta(hours=i), close=1.1+i/10000,
               high=1.11+i/10000, low=1.09+i/10000) for i in range(40)]
    monkeypatch.setattr(module, 'discover', lambda _: [{
        'instrument':'EURUSD','source':'oanda_v20','timeframe':'H1',
        'data_kind':'historical_real','last_timestamp':candles[-1].timestamp.isoformat(),
        'id':'oanda_v20:test','candles':candles,'quality_status':'imported_uncertified'}])
    result=module.build_historical_evidence('EURUSD')
    assert result['provenance']['historical_only'] is True
    assert result['provenance']['quality_certified'] is False
    assert result['verified_context']['technical']['observations']==40
    assert result['verified_context']['technical']['not_live'] is True


def test_no_historical_data_fails_closed(monkeypatch):
    monkeypatch.setattr(module,'discover',lambda _: [])
    with pytest.raises(ValueError, match='No checksum-validated'):
        module.build_historical_evidence('GBPUSD')
