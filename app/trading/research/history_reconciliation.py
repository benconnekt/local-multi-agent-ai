"""Read-only imported OANDA historical reconciliation; NEVER certifies trading data."""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from app.trading.data.catalogue import discover

PAIRS = ('EURUSD', 'GBPUSD', 'USDJPY')
FRAMES = ('H1', 'M15')
FIELDS = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
STEP = {'H1': timedelta(hours=1), 'M15': timedelta(minutes=15)}
NY = ZoneInfo('America/New_York')
SAFE = dict(decision='NO_TRADE', research_only=True, quality_certified=False,
            research_signal_eligible=False, independently_certified=False)

def _utc(s: str) -> datetime:
    t = datetime.fromisoformat(s.replace('Z', '+00:00'))
    if t.tzinfo is None: raise ValueError('Naive timestamp')
    return t.astimezone(timezone.utc)

def _market_open(t: datetime) -> bool:
    """Provisional FX Sun 17:00 through Fri before 17:00 New York local."""
    ny = t.astimezone(NY)
    return (ny.weekday() < 4 or (ny.weekday() == 4 and ny.hour < 17)
            or (ny.weekday() == 6 and ny.hour >= 17))

def _inspect(meta_path: Path) -> dict[str, Any]:
    csv_path = meta_path.with_suffix('.csv')
    record: dict[str, Any] = {'file': meta_path.name, 'csv': csv_path.name, 'ok': False, 'issues': []}
    try:
        meta = json.loads(meta_path.read_text(encoding='utf-8'))
        if not isinstance(meta, dict): raise ValueError('metadata_not_object')
        pair, tf = meta.get('instrument'), meta.get('timeframe')
        record.update(instrument=pair, timeframe=tf)
        if pair not in PAIRS or tf not in FRAMES: raise ValueError('unexpected_pair_or_timeframe')
        if (meta.get('provider'), meta.get('data_kind'), meta.get('environment'), meta.get('price_component'),
            meta.get('smoothed'), meta.get('strategy_eligible')) != ('oanda_v20', 'historical_real', 'practice', 'mid', False, False):
            raise ValueError('unsafe_or_unexpected_metadata')
        if meta.get('api_host') != 'https://api-fxpractice.oanda.com': raise ValueError('unexpected_host')
        if not csv_path.is_file(): raise ValueError('missing_csv')
        raw = csv_path.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        record['sha256'] = digest
        if digest != meta.get('csv_sha256'): raise ValueError('checksum_mismatch')
        with csv_path.open(newline='', encoding='utf-8') as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames != FIELDS: raise ValueError('unexpected_csv_columns')
            rows = list(reader)
        if not rows or len(rows) != meta.get('count'): raise ValueError('count_mismatch_or_empty')
        prev = None
        candles = []
        for row in rows:
            ts = _utc(row['timestamp'])
            if prev is not None and ts <= prev: raise ValueError('unordered_or_duplicate_timestamps')
            prev = ts
            values = tuple(float(row[k]) for k in ('open', 'high', 'low', 'close'))
            op, hi, lo, cl = values
            from math import isfinite
            if not all(isfinite(v) and v > 0 for v in values) or not (lo <= min(op, cl) <= max(op, cl) <= hi):
                raise ValueError('invalid_ohlc')
            candles.append((ts, values, row['volume']))
        if (_utc(meta['first_timestamp']) != candles[0][0] or
            _utc(meta['last_timestamp']) != candles[-1][0]): raise ValueError('timestamp_bounds_mismatch')
        record.update(ok=True, count=len(candles), first=candles[0][0].isoformat(),
                      last=candles[-1][0].isoformat(), candles=candles)
    except (OSError, ValueError, TypeError, KeyError, csv.Error) as exc:
        record['issues'].append(str(exc))
    return record

def reconcile(directory: Path) -> dict[str, Any]:
    """directory is historical_oanda or its forex parent; never writes to input."""
    folder = directory if directory.name == 'historical_oanda' else directory / 'historical_oanda'
    if not folder.is_dir(): raise FileNotFoundError(f'Missing historical import folder: {folder}')
    metas = sorted(folder.glob('*.json'))
    csvs = {p.stem for p in folder.glob('*.csv')}
    other_files = sorted(p.name for p in folder.iterdir() if p.is_file() and p.suffix not in ('.json', '.csv'))
    orphan_csv = sorted(csvs - {p.stem for p in metas})
    inspected = [_inspect(p) for p in metas]
    catalogued = {e['id'] for e in discover(folder) if e['source'] == 'oanda_v20'}
    merged: dict[tuple[str, str], dict[datetime, tuple]] = defaultdict(dict)
    problems: list[dict[str, Any]] = []
    counts = Counter()
    for rec in inspected:
        if not rec['ok']:
            problems.append({'file': rec['file'], 'issues': rec['issues']}); continue
        pair, tf = rec['instrument'], rec['timeframe']
        counts[(pair, tf)] += 1
        expected_id = 'oanda_v20:' + Path(rec['file']).stem
        if expected_id not in catalogued:
            problems.append({'file': rec['file'], 'issues': ['catalogue_rejected']})
        for ts, values, volume in rec.pop('candles'):
            previous = merged[(pair, tf)].get(ts)
            signature = (values, volume)
            if previous is not None and previous != signature:
                problems.append({'file': rec['file'], 'issues': ['conflicting_overlap'], 'timestamp': ts.isoformat()})
            merged[(pair, tf)].setdefault(ts, signature)
    if orphan_csv: problems.append({'issues': ['orphan_csv'], 'files': orphan_csv})
    if other_files: problems.append({'issues': ['unexpected_files'], 'files': other_files})
    summaries = {}
    for pair in PAIRS:
        for tf in FRAMES:
            series = sorted(merged[(pair, tf)])
            gaps = []
            if series:
                step = STEP[tf]
                # Count expected slots between the first and last observed candle.
                # This is a provisional schedule, not an authoritative holiday calendar.
                present = set(series)
                cursor = series[0]
                missing = 0
                while cursor <= series[-1]:
                    if _market_open(cursor) and cursor not in present:
                        missing += 1
                        if len(gaps) < 25: gaps.append(cursor.isoformat())
                    cursor += step
            else: missing = 0
            summaries[f'{pair}_{tf}'] = dict(chunks=counts[(pair, tf)], candles=len(series),
                first=series[0].isoformat() if series else None,
                last=series[-1].isoformat() if series else None,
                provisional_missing_market_slots=missing, missing_examples_utc=gaps)
    h4 = {}
    for pair in PAIRS:
        h1 = set(merged[(pair, 'H1')])
        groups = defaultdict(set)
        for ts in h1:
            boundary = ts.replace(hour=ts.hour // 4 * 4, minute=0, second=0, microsecond=0)
            groups[boundary].add(ts)
        complete = sum(all(start + timedelta(hours=i) in group for i in range(4))
                       for start, group in groups.items())
        h4[pair] = {'complete_utc_four_hour_groups': complete,
                    'incomplete_or_boundary_groups': len(groups) - complete,
                    'convention': 'UTC 00/04/08/12/16/20; provisional'}
    return {**SAFE, 'directory': str(folder), 'files_total': len([p for p in folder.iterdir() if p.is_file()]),
        'metadata_files': len(metas), 'csv_files': len(csvs), 'catalogued_oanda_datasets': len(catalogued),
        'orphan_csv': orphan_csv, 'unexpected_files': other_files,
        'files': inspected, 'series': summaries, 'h4': h4,
        'integrity_pass': not problems and all(s['candles'] for s in summaries.values()),
        'provisional_continuity_pass': all(s['provisional_missing_market_slots'] == 0 for s in summaries.values()),
        'problems': problems,
        'certification_readiness': 'NOT_CERTIFIED',
        'limitations': ['Provisional NY Forex session calendar; no independent holidays or provider outage certification',
                        'UTC H4 convention not independently certified',
                        'Catalogue discovery can silently skip files; mismatches are reported here',
                        'Integrity and continuity are not permission to trade']}

def main() -> None:
    p = argparse.ArgumentParser(description='Read-only OANDA historical reconciliation')
    p.add_argument('--directory', type=Path, default=Path('data/forex/historical_oanda'))
    p.add_argument('--output', type=Path, default=Path('reports/trading/history_reconciliation.json'))
    args = p.parse_args()
    report = reconcile(args.directory)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print('Files:', report['files_total'], 'Metadata:', report['metadata_files'], 'CSV:', report['csv_files'])
    print('Catalogue datasets:', report['catalogued_oanda_datasets'])
    for key, summary in report['series'].items():
        print(key, 'chunks:', summary['chunks'], 'candles:', summary['candles'],
              'provisional_missing_slots:', summary['provisional_missing_market_slots'])
    print('Integrity:', report['integrity_pass'], 'Continuity:', report['provisional_continuity_pass'],
          'Problems:', len(report['problems']), 'NO_TRADE')
    print('Report:', args.output)

if __name__ == '__main__': main()
