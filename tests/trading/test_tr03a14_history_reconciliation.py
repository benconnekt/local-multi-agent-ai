import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from app.trading.research.history_reconciliation import _market_open, reconcile


def _write(folder: Path, *, bad_hash=False):
    folder.mkdir(parents=True, exist_ok=True)
    stem = 'EURUSD_H1_2026-10-01_2026-10-01'
    raw = ('timestamp,open,high,low,close,volume\n'
           '2026-10-01T00:00:00+00:00,1.0,1.2,0.9,1.1,10\n').encode()
    (folder / (stem + '.csv')).write_bytes(raw)
    meta = dict(provider='oanda_v20', data_kind='historical_real', environment='practice',
                price_component='mid', smoothed=False, strategy_eligible=False,
                api_host='https://api-fxpractice.oanda.com', instrument='EURUSD',
                timeframe='H1', count=1, first_timestamp='2026-10-01T00:00:00+00:00',
                last_timestamp='2026-10-01T00:00:00+00:00',
                csv_sha256='wrong' if bad_hash else hashlib.sha256(raw).hexdigest())
    (folder / (stem + '.json')).write_text(json.dumps(meta))
    return stem


def test_hash_failure_is_reported(tmp_path):
    folder = tmp_path / 'historical_oanda'
    _write(folder, bad_hash=True)
    with patch('app.trading.research.history_reconciliation.discover', return_value=[]):
        report = reconcile(folder)
    assert report['integrity_pass'] is False
    assert any('checksum_mismatch' in p['issues'] for p in report['problems'])
    assert report['decision'] == 'NO_TRADE'


def test_orphan_csv_is_reported(tmp_path):
    folder = tmp_path / 'historical_oanda'
    stem = _write(folder)
    (folder / 'orphan.csv').write_text('unused')
    with patch('app.trading.research.history_reconciliation.discover', return_value=[{'id':'oanda_v20:'+stem, 'source':'oanda_v20'}]):
        report = reconcile(folder)
    assert report['orphan_csv'] == ['orphan']
    assert report['integrity_pass'] is False


def test_ny_weekend_dst_schedule():
    assert _market_open(datetime(2026, 10, 30, 20, tzinfo=timezone.utc))
    assert not _market_open(datetime(2026, 10, 31, 12, tzinfo=timezone.utc))
    assert _market_open(datetime(2026, 11, 1, 22, tzinfo=timezone.utc))
