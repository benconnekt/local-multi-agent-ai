"""Conservative, non-authorising closed-candle and freshness diagnostics.

Input must be provider-scoped, reconciled historical rows. This module does not
validate independent session calendars or grant trading eligibility.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Iterable

from app.trading.quality.h4_integrity import analyse_h4

HOUR = timedelta(hours=1)
QUARTER = timedelta(minutes=15)
H4 = timedelta(hours=4)


def _utc(value: Any) -> datetime:
    if isinstance(value, str):
        value = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise ValueError('Timestamp must be timezone-aware')
    return value.astimezone(timezone.utc)


def _ts(row: Any) -> datetime:
    value = row.model_dump() if hasattr(row, 'model_dump') else row
    return _utc(value['timestamp'])


def evaluate_freshness(
    h1_rows: Iterable[Any], m15_rows: Iterable[Any], *,
    as_of: datetime | str, minimum_h4: int = 250,
) -> dict[str, Any]:
    """Report completed bars and freshness without authorising research signals.

    Freshness is measured against the latest *expected* closed UTC bucket and
    provisional market hours. A separate session audit remains mandatory.
    """
    if minimum_h4 < 200:
        raise ValueError('H4 EMA200 requires at least 200 candles')
    cutoff = _utc(as_of)
    h1 = sorted(set(t for r in h1_rows if (t := _ts(r)) + HOUR <= cutoff))
    m15 = sorted(set(t for r in m15_rows if (t := _ts(r)) + QUARTER <= cutoff))
    h4_groups: dict[datetime, set[datetime]] = {}
    for t in h1:
        bucket = t.replace(hour=(t.hour // 4) * 4, minute=0, second=0, microsecond=0)
        h4_groups.setdefault(bucket, set()).add(t)
    complete_h4 = sorted(bucket for bucket, observed in h4_groups.items()
                         if bucket + H4 <= cutoff and observed == {bucket + i * HOUR for i in range(4)})
    integrity = analyse_h4([{'timestamp': t} for t in h1], minimum_h4=minimum_h4)
    latest = {'H4': complete_h4[-1] + H4 if complete_h4 else None,
              'H1': h1[-1] + HOUR if h1 else None,
              'M15': m15[-1] + QUARTER if m15 else None}
    # Conservative elapsed-time checks. Market closures can make these stale;
    # they must never be used to claim certified readiness.
    limits = {'H4': H4, 'H1': HOUR, 'M15': QUARTER}
    stale = {tf: end is None or cutoff - end > limits[tf] for tf, end in latest.items()}
    overlap = bool(h1 and m15 and max(h1[0], m15[0]) < min(h1[-1] + HOUR, m15[-1] + QUARTER))
    reasons = []
    if not overlap:
        reasons.append('no_H1_M15_overlap')
    if len(complete_h4) < minimum_h4:
        reasons.append('insufficient_H4_warmup')
    if integrity['status'] == 'invalid_source':
        reasons.append('missing_in_session_H1')
    for tf in ('H4', 'H1', 'M15'):
        if stale[tf]:
            reasons.append(f'stale_or_missing_{tf}')
    return {
        'as_of_utc': cutoff.isoformat(),
        'latest_closed_utc': {tf: end.isoformat() if end else None for tf, end in latest.items()},
        'stale': stale, 'overlapping_coverage': overlap,
        'complete_h4_candles': len(complete_h4), 'required_h4_candles': minimum_h4,
        'h4_warmup_sufficient': len(complete_h4) >= minimum_h4,
        'h4_integrity': integrity, 'blocking_reasons': reasons,
        'provisional_checks_pass': not reasons,
        'certified': False, 'research_signal_eligible': False,
        'research_only': True, 'quality_certified': False, 'decision': 'NO_TRADE',
    }
