"""Discover checksum-validated Yahoo and OANDA historical candle datasets.

Discovery is observational: validation never grants trading eligibility.
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
from pathlib import Path

from app.trading.data.models import Candle

STEM = re.compile(r"^(EURUSD|GBPUSD|USDJPY)_(M15|H1|H4|D1)_(\d{4}-\d{2}-\d{2})_(\d{4}-\d{2}-\d{2})$")
FIELDS = ['timestamp', 'open', 'high', 'low', 'close', 'volume']


def _locations(directory: Path) -> list[Path]:
    """Accept an existing dataset folder or its forex parent without double scanning."""
    if directory.name in ('historical_real', 'historical_oanda'):
        return [directory.parent / 'historical_real', directory.parent / 'historical_oanda']
    return [directory] if directory.is_dir() and any(directory.glob('*.json')) else [directory / 'historical_real', directory / 'historical_oanda']


def discover(directory: Path) -> list[dict]:
    results: list[dict] = []
    for folder in _locations(directory):
        if not folder.is_dir():
            continue
        for metadata_path in sorted(folder.glob('*.json')):
            match = STEM.fullmatch(metadata_path.stem)
            if not match:
                continue
            csv_path = metadata_path.with_suffix('.csv')
            try:
                meta = json.loads(metadata_path.read_text(encoding='utf-8'))
                if not isinstance(meta, dict) or not csv_path.is_file():
                    continue
                provider = meta.get('provider')
                if provider not in ('yahoo_finance', 'oanda_v20') or meta.get('data_kind') != 'historical_real':
                    continue
                symbol, timeframe, start, end = match.groups()
                if meta.get('symbol') != symbol or meta.get('timeframe') != timeframe:
                    continue
                if provider == 'yahoo_finance':
                    if folder.name == 'historical_oanda':
                        continue
                    if (str(meta.get('start_utc', ''))[:10], str(meta.get('end_utc_exclusive', ''))[:10]) != (start, end):
                        continue
                else:
                    if folder.name != 'historical_oanda':
                        continue
                    if (meta.get('environment'), meta.get('api_host'), meta.get('instrument'), meta.get('price_component'), meta.get('smoothed'), meta.get('strategy_eligible')) != ('practice', 'https://api-fxpractice.oanda.com', symbol, 'mid', False, False):
                        continue
                    if timeframe not in ('H1', 'M15'):
                        continue
                    if (str(meta.get('first_timestamp', ''))[:10], str(meta.get('last_timestamp', ''))[:10]) != (start, end):
                        continue
                raw = csv_path.read_bytes()
                if hashlib.sha256(raw).hexdigest() != meta.get('csv_sha256'):
                    continue
                with csv_path.open(newline='', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    if reader.fieldnames != FIELDS:
                        continue
                    candles = [Candle.model_validate({**row, 'volume': row['volume'] or None}) for row in reader]
                if not candles or len(candles) != meta.get('count'):
                    continue
                if any(b.timestamp <= a.timestamp for a, b in zip(candles, candles[1:])):
                    continue
                if candles[0].timestamp.tzinfo is None or any(c.timestamp.tzinfo is None for c in candles):
                    continue
                first = candles[0].timestamp.isoformat()
                last = candles[-1].timestamp.isoformat()
                if first != meta.get('first_timestamp') or last != meta.get('last_timestamp'):
                    continue
                results.append({
                    'id': f'oanda_v20:{metadata_path.stem}' if provider == 'oanda_v20' else metadata_path.stem,
                    'instrument': symbol, 'timeframe': timeframe,
                    'source': provider, 'data_kind': 'historical_real',
                    'quality_status': meta.get('quality_status', 'uncertified'),
                    'retrieved_at_utc': meta.get('retrieved_at_utc'),
                    'count': len(candles), 'first_timestamp': first,
                    'last_timestamp': last, 'candles': candles,
                    'price_component': meta.get('price_component'),
                    'environment': meta.get('environment'),
                    'strategy_eligible': False,
                })
            except (OSError, ValueError, TypeError, KeyError, csv.Error):
                continue
    return results
