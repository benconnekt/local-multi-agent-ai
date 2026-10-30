"""Discover and validate local historical datasets without mixing provenance."""
from __future__ import annotations
import csv
import hashlib
import json
import re
from pathlib import Path
from app.trading.data.models import Candle, Instrument, Timeframe

STEM = re.compile(r"^(EURUSD|GBPUSD|USDJPY)_(M15|H1|H4|D1)_(\d{4}-\d{2}-\d{2})_(\d{4}-\d{2}-\d{2})$")


def discover(directory: Path) -> list[dict]:
    results = []
    if not directory.exists():
        return results
    for metadata_path in sorted(directory.glob('*.json')):
        match = STEM.fullmatch(metadata_path.stem)
        if not match:
            continue
        csv_path = metadata_path.with_suffix('.csv')
        try:
            meta = json.loads(metadata_path.read_text(encoding='utf-8'))
            if not isinstance(meta, dict) or not csv_path.is_file():
                continue
            if meta.get('provider') != 'yahoo_finance' or meta.get('data_kind') != 'historical_real':
                continue
            symbol, timeframe, start, end = match.groups()
            if (meta.get('symbol'), meta.get('timeframe'), meta.get('start_utc', '')[:10], meta.get('end_utc_exclusive', '')[:10]) != (symbol, timeframe, start, end):
                continue
            raw = csv_path.read_bytes()
            if hashlib.sha256(raw).hexdigest() != meta.get('csv_sha256'):
                continue
            candles = []
            with csv_path.open(newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                if reader.fieldnames != ['timestamp', 'open', 'high', 'low', 'close', 'volume']:
                    continue
                for row in reader:
                    candles.append(Candle.model_validate({**row, 'volume': row['volume'] or None}))
            if not candles or len(candles) != meta.get('count'):
                continue
            if any(b.timestamp <= a.timestamp for a, b in zip(candles, candles[1:])):
                continue
            if candles[0].timestamp.isoformat() != meta.get('first_timestamp') or candles[-1].timestamp.isoformat() != meta.get('last_timestamp'):
                continue
            results.append({'id': metadata_path.stem, 'instrument': symbol, 'timeframe': timeframe,
                            'source': 'yahoo_finance', 'data_kind': 'historical_real',
                            'quality_status': meta.get('quality_status', 'uncertified'),
                            'retrieved_at_utc': meta.get('retrieved_at_utc'), 'count': len(candles),
                            'first_timestamp': candles[0].timestamp.isoformat(),
                            'last_timestamp': candles[-1].timestamp.isoformat(), 'candles': candles})
        except (OSError, ValueError, TypeError, KeyError, csv.Error):
            continue
    return results
