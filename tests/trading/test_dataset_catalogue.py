import csv
import hashlib
import json
from pathlib import Path
from app.trading.data.catalogue import discover


def test_discovery_checks_hash_and_provenance(tmp_path: Path):
    stem = 'EURUSD_H1_2026-10-20_2026-10-21'
    csv_path = tmp_path / f'{stem}.csv'
    with csv_path.open('w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['timestamp','open','high','low','close','volume'])
        writer.writerow(['2026-10-20T00:00:00Z',1.1,1.2,1.0,1.15,''])
    metadata = {'provider':'yahoo_finance','data_kind':'historical_real','symbol':'EURUSD','timeframe':'H1',
                'start_utc':'2026-10-20T00:00:00+00:00','end_utc_exclusive':'2026-10-21T00:00:00+00:00',
                'csv_sha256':hashlib.sha256(csv_path.read_bytes()).hexdigest(),'count':1,
                'first_timestamp':'2026-10-20T00:00:00+00:00','last_timestamp':'2026-10-20T00:00:00+00:00'}
    (tmp_path / f'{stem}.json').write_text(json.dumps(metadata))
    assert len(discover(tmp_path)) == 1
    csv_path.write_text('tampered')
    assert discover(tmp_path) == []
