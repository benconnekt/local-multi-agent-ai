
"""Read-only OANDA historical backfill; never enables strategy signals."""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import urllib.error
import urllib.parse
import urllib.request

from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(PROJECT_ROOT / ".env")

OANDA_HOSTS = {
    "practice": "https://api-fxpractice.oanda.com",
    "live": "https://api-fxtrade.oanda.com",
}

def get_oanda_environment() -> str:
    environment = os.getenv(
        "OANDA_ENVIRONMENT", "practice"
    ).strip().lower()

    if environment not in OANDA_HOSTS:
        raise ValueError(
            f"Unsupported OANDA_ENVIRONMENT: {environment}"
        )

    if environment == "live":
        raise RuntimeError(
            "Live OANDA access is disabled in research mode"
        )

    return environment

OANDA_ENVIRONMENT = get_oanda_environment()
HOST = OANDA_HOSTS[OANDA_ENVIRONMENT]
OANDA_API_TOKEN = os.getenv("OANDA_API_TOKEN")
INSTRUMENTS = {'EURUSD': 'EUR_USD', 'GBPUSD': 'GBP_USD', 'USDJPY': 'USD_JPY'}
GRANULARITIES = ('H1', 'M15')
FIELDS = ('timestamp', 'open', 'high', 'low', 'close', 'volume')


def parse_candles(payload: dict, *, instrument: str, granularity: str) -> list[dict]:
    if payload.get('instrument') != INSTRUMENTS[instrument] or payload.get('granularity') != granularity:
        raise ValueError('OANDA response instrument/granularity mismatch')
    rows = []
    for candle in payload.get('candles', []):
        if candle.get('complete') is not True:
            continue
        mid = candle.get('mid')
        if not isinstance(mid, dict):
            raise ValueError('Missing midpoint candle data')
        ts = datetime.fromisoformat(candle['time'].replace('Z', '+00:00'))
        if ts.tzinfo is None:
            raise ValueError('Naive OANDA timestamp')
        ts = ts.astimezone(timezone.utc)
        prices = [float(mid[k]) for k in ('o', 'h', 'l', 'c')]
        op, hi, lo, cl = prices
        if not (0 < lo <= min(op, cl) <= max(op, cl) <= hi):
            raise ValueError('Invalid OHLC data')
        rows.append(dict(zip(FIELDS, (ts.isoformat(), mid['o'], mid['h'], mid['l'], mid['c'], str(candle['volume'])))))
    if any(a['timestamp'] >= b['timestamp'] for a, b in zip(rows, rows[1:])):
        raise ValueError('Unordered or duplicate OANDA candles')
    return rows


def fetch_candles(token: str, instrument: str, granularity: str, count: int) -> list[dict]:
    if instrument not in INSTRUMENTS or granularity not in GRANULARITIES or not 1 <= count <= 5000:
        raise ValueError('Unsupported request')
    query = urllib.parse.urlencode({'granularity': granularity, 'price': 'M', 'smooth': 'false', 'count': count})
    url = f'{HOST}/v3/instruments/{INSTRUMENTS[instrument]}/candles?{query}'
    request = urllib.request.Request(url, headers={'Authorization': f'Bearer {token}', 'Accept': 'application/json'})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.load(response)
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f'OANDA HTTP {exc.code}; check practice credentials and API access') from None
    return parse_candles(payload, instrument=instrument, granularity=granularity)


def save_candles(rows: list[dict], *, instrument: str, granularity: str, directory: Path) -> tuple[Path, Path]:
    if not rows:
        raise ValueError('No complete candles received')
    directory.mkdir(parents=True, exist_ok=True)
    start = rows[0]['timestamp'][:10]
    end = rows[-1]['timestamp'][:10]
    stem = f'{instrument}_{granularity}_{start}_{end}'
    csv_path = directory / f'{stem}.csv'
    meta_path = directory / f'{stem}.json'
    if csv_path.exists() or meta_path.exists():
        raise FileExistsError(f'Refusing to overwrite existing dataset: {stem}')
    import io
    buffer = io.StringIO(newline='')
    writer = csv.DictWriter(buffer, fieldnames=FIELDS, lineterminator='\n')
    writer.writeheader()
    writer.writerows(rows)
    raw = buffer.getvalue().encode('utf-8')
    
    metadata = {
        "provider": "oanda_v20",
        "environment": OANDA_ENVIRONMENT,
        "api_host": HOST,
        "data_kind": "historical_real",
        "instrument": instrument,
        "symbol": instrument,
        "timeframe": granularity,
        "price_component": "mid",
        "smoothed": False,
        "quality_status": "imported_uncertified",
        "count": len(rows),
        "first_timestamp": rows[0]["timestamp"],
        "last_timestamp": rows[-1]["timestamp"],
        "csv_sha256": hashlib.sha256(raw).hexdigest(),
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "strategy_eligible": False,
    }

    csv_path.write_bytes(raw)
    meta_path.write_text(json.dumps(metadata, indent=2) + '\n', encoding='utf-8')
    return csv_path, meta_path


def main() -> None:
    parser = argparse.ArgumentParser(description='Read-only OANDA practice candle backfill')
    parser.add_argument('--instrument', choices=INSTRUMENTS, required=True)
    parser.add_argument('--count', type=int, default=2500)
    parser.add_argument('--directory', type=Path, default=Path('data/forex/historical_oanda'))
    args = parser.parse_args()
    token = os.environ.get('OANDA_API_TOKEN')
    if not token:
        parser.error('Set OANDA_API_TOKEN in your local environment (never commit it)')
    for tf in GRANULARITIES:
        rows = fetch_candles(token, args.instrument, tf, args.count)
        csv_path, _ = save_candles(rows, instrument=args.instrument, granularity=tf, directory=args.directory)
        print(f'{tf}: saved {len(rows)} complete candles to {csv_path}; UNCERTIFIED')
    print('Research signals remain disabled. OANDA data is not yet admitted to the verified catalogue.')


if __name__ == '__main__':
    main()
