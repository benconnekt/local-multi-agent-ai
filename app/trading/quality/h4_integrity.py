"""Non-authorising UTC H4 integrity and closed-candle coverage diagnostics."""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any, Iterable

from app.trading.quality.fx_session_validation import _market_open

HOUR = timedelta(hours=1)
QUARTER = timedelta(minutes=15)


def _utc(value: Any) -> datetime:
    if isinstance(value, str):
        value = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise ValueError('Timestamp must be timezone-aware')
    return value.astimezone(timezone.utc)


def _row(value: Any) -> dict:
    return value.model_dump() if hasattr(value, 'model_dump') else value


def analyse_h4(h1_rows: Iterable[Any], *, minimum_h4: int = 200, max_examples: int = 12) -> dict:
    """Classify incomplete UTC H4 buckets without manufacturing partial bars."""
    if minimum_h4 < 1 or max_examples < 0:
        raise ValueError('Invalid analysis limits')
    slots: dict[datetime, set[datetime]] = defaultdict(set)
    for raw in h1_rows:
        ts = _utc(_row(raw)['timestamp'])
        bucket = ts.replace(hour=(ts.hour // 4) * 4, minute=0, second=0, microsecond=0)
        slots[bucket].add(ts)
    complete = 0
    reasons = {'session_boundary': 0, 'dataset_boundary': 0, 'missing_in_session': 0}
    examples = []
    first = min((t for s in slots.values() for t in s), default=None)
    last = max((t for s in slots.values() for t in s), default=None)
    for bucket, observed in sorted(slots.items()):
        expected = [bucket + HOUR * i for i in range(4)]
        if observed == set(expected):
            complete += 1
            continue
        missing = [ts for ts in expected if ts not in observed]
        if any(_market_open(ts) and first <= ts <= last for ts in missing):
            category = 'missing_in_session'
        elif any(_market_open(ts) for ts in missing):
            category = 'dataset_boundary'
        else:
            category = 'session_boundary'
        reasons[category] += 1
        if len(examples) < max_examples:
            examples.append({'bucket_utc': bucket.isoformat(), 'classification': category,
                             'observed_hours': len(observed),
                             'missing_hours_utc': [ts.isoformat() for ts in missing]})
    return {'source': 'derived_from_H1', 'complete_candles': complete,
            'incomplete_groups': sum(reasons.values()), 'incomplete_reasons': reasons,
            'incomplete_examples': examples, 'minimum_h4_candles': minimum_h4,
            'history_sufficient': complete >= minimum_h4,
            'status': 'invalid_source' if reasons['missing_in_session'] else
                      'pending_independent_certification',
            'independently_certified': False}


def closed_timeframe_alignment(h1_rows: Iterable[Any], m15_rows: Iterable[Any], *,
                               as_of: datetime | str, minimum_h4: int = 200) -> dict:
    """Check simultaneous closed-candle availability; never authorises signals."""
    cutoff = _utc(as_of)
    h1 = sorted({_utc(_row(r)['timestamp']) for r in h1_rows if _utc(_row(r)['timestamp']) + HOUR <= cutoff})
    m15 = sorted({_utc(_row(r)['timestamp']) for r in m15_rows if _utc(_row(r)['timestamp']) + QUARTER <= cutoff})
    h4 = analyse_h4([{'timestamp': t} for t in h1], minimum_h4=minimum_h4)
    overlap = bool(h1 and m15 and max(h1[0], m15[0]) < min(h1[-1] + HOUR, m15[-1] + QUARTER))
    aligned = bool(h1 and m15 and h1[-1] + HOUR <= cutoff and m15[-1] + QUARTER <= cutoff)
    return {'as_of_utc': cutoff.isoformat(), 'overlapping_coverage': overlap,
            'closed_candles_only': aligned, 'h4_complete_candles': h4['complete_candles'],
            'h4_history_sufficient': h4['history_sufficient'],
            'ready_for_certification_review': bool(overlap and aligned and h4['history_sufficient']
                                                  and h4['status'] != 'invalid_source'),
            'certified': False, 'research_signal_eligible': False}
