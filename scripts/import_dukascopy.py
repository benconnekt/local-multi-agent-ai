"""Usage: uv run python scripts/import_dukascopy.py EURUSD 2026-10-20 2026-10-21"""
from __future__ import annotations

import argparse
import csv
from datetime import date, datetime, timedelta, timezone
import json
from pathlib import Path
import sys

# Allow direct invocation from repository root without installing a package.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.trading.data.providers.dukascopy import SCALES, ImportErrorData, aggregate, decode_bi5, fetch_hour

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'data' / 'forex' / 'historical_real'


def run(symbol: str, start: date, end: date, output: Path = OUTPUT) -> None:
    if symbol not in SCALES:
        raise ImportErrorData('Unsupported instrument')
    if end <= start or (end - start).days > 7:
        raise ImportErrorData('End must be after start, with at most 7 days per import')
    if end > datetime.now(timezone.utc).date():
        raise ImportErrorData('Cannot import future dates')
    ticks = []
    missing = []
    current = datetime.combine(start, datetime.min.time(), timezone.utc)
    until = datetime.combine(end, datetime.min.time(), timezone.utc)
    while current < until:
        raw = fetch_hour(symbol, current)
        if raw is None:
            missing.append(current.isoformat())
        else:
            ticks.extend(decode_bi5(raw, current, symbol))
        current += timedelta(hours=1)
    if not ticks:
        raise ImportErrorData('No ticks retrieved; no files written')
    if missing:
        raise ImportErrorData(f'{len(missing)} hourly files missing (including possible market closure). Refusing incomplete import; first: {missing[0]}')
    # An empty returned archive is not a verified complete market interval.
    hours_with_ticks = {tick.timestamp.replace(minute=0, second=0, microsecond=0) for tick in ticks}
    expected_hours = int((until - datetime.combine(start, datetime.min.time(), timezone.utc)).total_seconds() / 3600)
    if len(hours_with_ticks) != expected_hours:
        raise ImportErrorData('At least one hourly archive had no ticks. Refusing incomplete import.')
    output.mkdir(parents=True, exist_ok=True)
    for timeframe, minutes in [('M15', 15), ('H1', 60)]:
        candles = aggregate(ticks, minutes)
        target = output / f'{symbol}_{timeframe}_{start}_{end}.csv'
        metadata = target.with_suffix('.json')
        if target.exists() or metadata.exists():
            raise FileExistsError(f'Output exists; refusing overwrite: {target}')
        # Stage files and publish only after validation. The API does not yet consume these files.
        from app.trading.data.models import Candle
        for candle in candles:
            Candle.model_validate(candle)
        staged = target.with_suffix('.csv.tmp')
        try:
            with staged.open('x', newline='', encoding='utf-8') as stream:
                writer = csv.DictWriter(stream, fieldnames=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                writer.writeheader()
                writer.writerows(candles)
            staged.rename(target)
            metadata.write_text(json.dumps({'source': 'Dukascopy historical tick archive', 'data_kind': 'historical', 'price_side': 'bid', 'volume_kind': 'sum_of_reported_bid_tick_volume', 'timezone': 'UTC', 'instrument': symbol, 'timeframe': timeframe, 'start_inclusive': start.isoformat(), 'end_exclusive': end.isoformat(), 'candles': len(candles), 'research_only': True}, indent=2) + '\n')
        finally:
            staged.unlink(missing_ok=True)
        print(f'Imported {len(candles)} {timeframe} candles: {target}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Import a complete UTC weekday range from Dukascopy, research only')
    parser.add_argument('symbol', choices=sorted(SCALES))
    parser.add_argument('start', type=date.fromisoformat, help='UTC start date (inclusive)')
    parser.add_argument('end', type=date.fromisoformat, help='UTC end date (exclusive), max 7 days')
    args = parser.parse_args()
    try:
        run(args.symbol, args.start, args.end)
    except (ImportErrorData, FileExistsError) as exc:
        parser.exit(1, f'Import refused: {exc}\n')
