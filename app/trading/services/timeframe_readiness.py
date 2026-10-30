"""Provider-scoped, non-authorising historical timeframe diagnostics."""
from __future__ import annotations
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any

from app.trading.quality.h4_integrity import analyse_h4, closed_timeframe_alignment

STEPS = {'H1': timedelta(hours=1), 'M15': timedelta(minutes=15)}


def _timestamp(value: Any) -> datetime:
    if isinstance(value, str):
        value = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise ValueError('Timestamp must be timezone-aware')
    return value.astimezone(timezone.utc)


def _source_diagnostic(entries: list[dict], timeframe: str) -> tuple[dict, list[datetime]]:
    matching = [e for e in entries if e.get('timeframe') == timeframe]
    if not matching:
        return ({'source': 'historical_real', 'status': 'missing', 'dataset_ids': [],
                 'candle_count': 0, 'gap_count': None, 'conflict_count': None,
                 'certified': False, 'reason': f'No {timeframe} historical dataset'}, [])
    seen: dict[datetime, tuple] = {}
    conflicts = 0
    try:
        for dataset in matching:
            for candle in dataset['candles']:
                row = candle.model_dump() if hasattr(candle, 'model_dump') else candle
                ts = _timestamp(row['timestamp'])
                values = tuple(float(row[k]) for k in ('open', 'high', 'low', 'close')) + (None if row.get('volume') in (None, '') else float(row['volume']),)
                if ts in seen and seen[ts] != values:
                    conflicts += 1
                seen[ts] = values
        times = sorted(seen)
        step = STEPS[timeframe]
        gaps = sum(b - a != step for a, b in zip(times, times[1:]))
        aligned = all(t.minute % (15 if timeframe == 'M15' else 60) == 0 and t.second == 0 and t.microsecond == 0 for t in times)
    except (ValueError, KeyError, TypeError, OverflowError) as exc:
        return ({'source': 'historical_real', 'status': 'invalid',
                 'dataset_ids': [e['id'] for e in matching], 'candle_count': 0,
                 'gap_count': None, 'conflict_count': None, 'certified': False,
                 'reason': f'Invalid source candle: {exc}'}, [])
    status = 'pending_session_certification' if not conflicts and aligned else 'invalid'
    diagnostic = {'source': 'historical_real', 'status': status,
                  'dataset_ids': [e['id'] for e in matching], 'candle_count': len(times),
                  'gap_count': gaps, 'conflict_count': conflicts, 'timestamp_aligned': aligned,
                  'first_timestamp': times[0].isoformat() if times else None,
                  'last_timestamp': times[-1].isoformat() if times else None,
                  'certified': False,
                  'reason': 'Independent FX session calendar and provider coverage not certified' if status != 'invalid' else 'Conflicting or misaligned candles'}
    # Never derive H4 or cross-timeframe alignment from conflicting source candles.
    return diagnostic, ([] if conflicts else times)


def inspect_timeframes(entries: list[dict], *, h4_min_candles: int = 250,
                       provider: str | None = None) -> dict:
    if h4_min_candles < 200:
        raise ValueError('H4 EMA200 requires at least 200 candles')
    providers = {e.get('source') for e in entries if e.get('timeframe') in STEPS}
    if provider is None and len(providers) > 1:
        return {'provider': None, 'status': 'provider_selection_required',
                'H1': None, 'M15': None, 'H4': None,
                'alignment': {'overlapping_coverage': False, 'certified': False,
                              'reason': 'Multiple historical providers; explicit selection required'}}
    if provider is not None:
        if provider not in ('oanda_v20', 'yahoo_finance'):
            raise ValueError('Unsupported historical provider')
        entries = [e for e in entries if e.get('source') == provider]
    elif providers:
        provider = next(iter(providers))
    h1, h1_times = _source_diagnostic(entries, 'H1')
    m15, m15_times = _source_diagnostic(entries, 'M15')
    groups: dict[datetime, set[datetime]] = defaultdict(set)
    for ts in h1_times:
        bucket = ts.replace(hour=(ts.hour // 4) * 4, minute=0, second=0, microsecond=0)
        groups[bucket].add(ts)
    complete = [bucket for bucket, times in groups.items()
                if times == {bucket + timedelta(hours=i) for i in range(4)}]
    incomplete = len(groups) - len(complete)
    h4_status = ('invalid_source' if h1['status'] == 'invalid' else
                 'missing_source' if not h1_times else
                 'insufficient_history' if len(complete) < h4_min_candles else
                 'pending_session_certification')
    h4_integrity = analyse_h4([{'timestamp': ts} for ts in h1_times], minimum_h4=h4_min_candles)
    h4 = {'source': 'derived_from_H1', 'status': h4_status,
          'candle_count': len(complete), 'incomplete_groups': incomplete,
          'required_candles': h4_min_candles, 'certified': False,
          'reason': 'H4 is derived from H1; session/coverage certification remains pending'}
    h4['integrity'] = h4_integrity
    if h1_times and m15_times:
        overlap = max(min(h1_times), min(m15_times)) < min(max(h1_times) + STEPS['H1'], max(m15_times) + STEPS['M15'])
    else:
        overlap = False
    # Dataset ranges alone cannot prove synchronised closed-candle freshness.
    return {'provider': provider, 'H1': h1, 'M15': m15, 'H4': h4,
            'alignment': {'overlapping_coverage': overlap, 'certified': False,
                          'reason': 'Overlapping coverage alone does not certify synchronized closed candles'}}
