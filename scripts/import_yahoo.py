"""Import real Yahoo historical FX candles into a separate, attributed archive."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import sys
import tempfile
from datetime import date, datetime, time, timezone
from pathlib import Path

from app.trading.data.models import Instrument, Timeframe
from app.trading.data.providers.yahoo_provider import YahooDataError, YahooFinanceProvider

OUTPUT = Path("data/forex/historical_real")


def main() -> int:
    parser = argparse.ArgumentParser(description="Import Yahoo historical FX data (research only)")
    parser.add_argument("instrument", choices=[item.value for item in Instrument])
    parser.add_argument("timeframe", choices=["M15", "H1", "D1"])
    parser.add_argument("start", type=date.fromisoformat)
    parser.add_argument("end", type=date.fromisoformat, help="Exclusive end date")
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    start = datetime.combine(args.start, time.min, tzinfo=timezone.utc)
    end = datetime.combine(args.end, time.min, tzinfo=timezone.utc)
    try:
        candles = YahooFinanceProvider().load(Instrument(args.instrument), Timeframe(args.timeframe), start, end)
        args.output.mkdir(parents=True, exist_ok=True)
        stem = f"{args.instrument}_{args.timeframe}_{args.start}_{args.end}"
        csv_path = args.output / f"{stem}.csv"
        meta_path = args.output / f"{stem}.json"
        if csv_path.exists() or meta_path.exists():
            raise YahooDataError("Output already exists; refusing to overwrite")
        with tempfile.TemporaryDirectory(dir=args.output) as temp:
            staged = Path(temp) / csv_path.name
            with staged.open("w", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                writer.writerow(["timestamp", "open", "high", "low", "close", "volume"])
                for candle in candles:
                    writer.writerow([candle.timestamp.isoformat().replace("+00:00", "Z"), candle.open,
                                     candle.high, candle.low, candle.close, ""])
            digest = hashlib.sha256(staged.read_bytes()).hexdigest()
            metadata = {
                "provider": "yahoo_finance", "symbol": args.instrument,
                "provider_symbol": {"EURUSD": "EURUSD=X", "GBPUSD": "GBPUSD=X", "USDJPY": "JPY=X"}[args.instrument],
                "timeframe": args.timeframe, "start_utc": start.isoformat(), "end_utc_exclusive": end.isoformat(),
                "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
                "data_kind": "historical_real", "price_basis": "Yahoo indicative FX OHLC; not executable bid/ask",
                "count": len(candles), "first_timestamp": candles[0].timestamp.isoformat(),
                "last_timestamp": candles[-1].timestamp.isoformat(), "csv_sha256": digest,
                "quality_status": "validated_ohlc_not_completeness_certified",
            }
            staged_meta = Path(temp) / meta_path.name
            staged_meta.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
            # Publish metadata last; on an interrupted write, orphan CSV is never treated as verified.
            os.replace(staged, csv_path)
            os.replace(staged_meta, meta_path)
        print(f"Imported {len(candles)} candles: {csv_path}\nMetadata: {meta_path}")
        return 0
    except (YahooDataError, OSError, ValueError) as exc:
        print(f"Import refused: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
