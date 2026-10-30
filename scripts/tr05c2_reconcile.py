"""Read-only audit of imported OANDA history, with explicit provisional calendar."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
from pathlib import Path
from app.trading.data.catalogue import discover
from app.trading.quality.fx_session_validation import audit_sessions
from app.trading.quality.holiday_calendar import OANDA_OBSERVED_2025_2026_V1
from app.trading.quality.broker_absences import BROKER_OBSERVED_ABSENCES_V1


def utc(value):
    dt = value if isinstance(value, datetime) else datetime.fromisoformat(value.replace('Z', '+00:00'))
    if dt.tzinfo is None:
        raise ValueError('Naive timestamp')
    return dt.astimezone(timezone.utc)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--directory', default='data/forex/historical_real')
    args = parser.parse_args()
    entries = discover(Path(args.directory))
    for pair in ('EURUSD', 'GBPUSD', 'USDJPY'):
        for timeframe in ('H1', 'M15'):
            merged = {}
            conflicts = []
            for entry in entries:
                if not (entry['instrument'] == pair and entry['timeframe'] == timeframe and entry['source'] == 'oanda_v20' and entry['data_kind'] == 'historical_real'):
                    continue
                for candle in entry['candles']:
                    row = candle.model_dump() if hasattr(candle, 'model_dump') else candle
                    ts = utc(row['timestamp'])
                    signature = tuple(float(row[k]) for k in ('open','high','low','close'))
                    if ts in merged and merged[ts] != signature:
                        conflicts.append(ts.isoformat())
                    merged[ts] = signature
            rows = [dict(timestamp=ts, open=v[0], high=v[1], low=v[2], close=v[3]) for ts,v in sorted(merged.items())]
            report = audit_sessions(rows, timeframe, calendar=OANDA_OBSERVED_2025_2026_V1, acknowledged_absences=BROKER_OBSERVED_ABSENCES_V1.get(("oanda_v20", pair, timeframe), frozenset()))
            print(f'{pair} {timeframe}: PASS={report.provisional_schedule_pass and not conflicts} candles={len(rows)} excluded_provisional_closure={report.excluded_calendar_intervals} missing={report.missing_expected_candles} broker_observed_absences={report.acknowledged_absence_intervals} conflicts={len(conflicts)} unexpected={report.unexpected_session_candles}')
            if report.missing_examples: print('  missing:', ', '.join(report.missing_examples))
            if conflicts: print('  conflicting overlaps:', ', '.join(conflicts[:8]))
    print('Calendar remains UNVERIFIED. Audit PASS is not independent certification.')

if __name__ == '__main__':
    main()
