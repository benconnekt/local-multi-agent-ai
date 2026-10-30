import json
import pytest
from app.trading.data.oanda_backfill import parse_candles, save_candles


def payload(complete=True):
    return {'instrument': 'EUR_USD', 'granularity': 'H1', 'candles': [
        {'time': '2026-10-20T00:00:00.000000000Z', 'complete': complete, 'volume': 10,
         'mid': {'o': '1.1000', 'h': '1.1100', 'l': '1.0900', 'c': '1.1050'}}]}


def test_complete_only():
    assert len(parse_candles(payload(), instrument='EURUSD', granularity='H1')) == 1
    assert parse_candles(payload(False), instrument='EURUSD', granularity='H1') == []


def test_rejects_wrong_pair():
    with pytest.raises(ValueError, match='mismatch'):
        parse_candles(payload(), instrument='GBPUSD', granularity='H1')


def test_rejects_bad_ohlc():
    p = payload()
    p['candles'][0]['mid']['h'] = '1.0000'
    with pytest.raises(ValueError, match='OHLC'):
        parse_candles(p, instrument='EURUSD', granularity='H1')


def test_saves_uncertified_with_hash(tmp_path):
    rows = parse_candles(payload(), instrument='EURUSD', granularity='H1')
    csv_path, meta_path = save_candles(rows, instrument='EURUSD', granularity='H1', directory=tmp_path)
    import hashlib
    metadata = json.loads(meta_path.read_text())
    assert metadata['quality_status'] == 'imported_uncertified'
    assert metadata['strategy_eligible'] is False
    assert metadata['csv_sha256'] == hashlib.sha256(csv_path.read_bytes()).hexdigest()
    with pytest.raises(FileExistsError):
        save_candles(rows, instrument='EURUSD', granularity='H1', directory=tmp_path)
