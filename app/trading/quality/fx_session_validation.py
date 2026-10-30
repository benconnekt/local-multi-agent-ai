"""Conservative, non-authorising FX session audit with New York DST awareness."""
from __future__ import annotations
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone, time
from zoneinfo import ZoneInfo
from typing import Any, Iterable
from math import isfinite

STEPS = {'H1': timedelta(hours=1), 'M15': timedelta(minutes=15)}
UTC = timezone.utc
NY = ZoneInfo('America/New_York')

@dataclass(frozen=True)
class SessionAudit:
    timeframe: str
    candle_count: int
    first_timestamp: str | None
    last_timestamp: str | None
    missing_expected_candles: int
    missing_examples: tuple[str, ...]
    unexpected_session_candles: int
    duplicate_timestamps: int
    misaligned_timestamps: int
    invalid_ohlc: int
    checked_expected_intervals: int
    provisional_schedule_pass: bool
    independently_certified: bool = False
    schedule: str = 'provisional_new_york_sun_17_to_fri_17_dst_aware'
    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

def _utc(value: Any) -> datetime:
    if isinstance(value, datetime):
        dt = value
    elif isinstance(value, str):
        dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
    else:
        raise ValueError('Invalid timestamp')
    if dt.tzinfo is None:
        raise ValueError('Timestamp must be timezone-aware')
    return dt.astimezone(UTC)

def _market_open(ts: datetime) -> bool:
    """Provisional spot-FX week: Sunday 17:00 to Friday 17:00 America/New_York.

    This is NOT a verified OANDA holiday/maintenance calendar.
    """
    local = ts.astimezone(NY)
    day = local.weekday()
    clock = local.timetz().replace(tzinfo=None)
    return day <= 3 or (day == 4 and clock < time(17)) or (day == 6 and clock >= time(17))

def _valid_bar(bar: dict[str, Any]) -> bool:
    try:
        o, h, l, c = (float(bar[k]) for k in ('open', 'high', 'low', 'close'))
        return all(isfinite(x) for x in (o, h, l, c)) and 0 < l <= min(o, c) <= max(o, c) <= h
    except (KeyError, ValueError, TypeError):
        return False

def audit_sessions(rows: Iterable[Any], timeframe: str, *, max_examples: int = 8) -> SessionAudit:
    if timeframe not in STEPS:
        raise ValueError('Only H1 and M15 source timeframes are supported')
    if max_examples < 0:
        raise ValueError('max_examples must be nonnegative')
    step = STEPS[timeframe]
    timestamps: list[datetime] = []
    invalid_ohlc = 0
    for raw in rows:
        bar = raw.model_dump() if hasattr(raw, 'model_dump') else raw
        timestamps.append(_utc(bar['timestamp']))
        invalid_ohlc += not _valid_bar(bar)
    unique = sorted(set(timestamps))
    duplicates = len(timestamps) - len(unique)
    alignment = sum(bool(t.minute % (step.seconds // 60) or t.second or t.microsecond) for t in unique)
    unexpected = sum(not _market_open(t) for t in unique)
    missing = 0
    examples: list[str] = []
    checked = 0
    if unique:
        observed = set(unique)
        t = unique[0]
        while t <= unique[-1]:
            if _market_open(t):
                checked += 1
                if t not in observed:
                    missing += 1
                    if len(examples) < max_examples:
                        examples.append(t.isoformat())
            t += step
    passed = bool(unique) and not any((duplicates, alignment, unexpected, missing, invalid_ohlc))
    return SessionAudit(timeframe, len(timestamps), unique[0].isoformat() if unique else None,
                        unique[-1].isoformat() if unique else None, missing, tuple(examples),
                        unexpected, duplicates, alignment, invalid_ohlc, checked, passed)

def derive_h4_summary(h1_rows: Iterable[Any], *, minimum_h4: int = 200) -> dict[str, Any]:
    if minimum_h4 < 1:
        raise ValueError('minimum_h4 must be positive')
    groups: dict[datetime, set[datetime]] = {}
    for raw in h1_rows:
        bar = raw.model_dump() if hasattr(raw, 'model_dump') else raw
        ts = _utc(bar['timestamp'])
        bucket = ts.replace(hour=ts.hour // 4 * 4, minute=0, second=0, microsecond=0)
        groups.setdefault(bucket, set()).add(ts)
    complete = sum(all(bucket + timedelta(hours=i) in slots for i in range(4)) for bucket, slots in groups.items())
    return {'source': 'derived_from_H1', 'complete_candles': complete,
            'incomplete_groups': len(groups) - complete,
            'minimum_h4_candles': minimum_h4,
            'history_sufficient': complete >= minimum_h4,
            'independently_certified': False,
            'status': 'pending_independent_certification'}
