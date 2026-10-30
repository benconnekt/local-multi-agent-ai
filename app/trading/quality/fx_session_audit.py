"""Conservative FX session *diagnostics*, not independent market certification.

Assumption: weekly FX market opens Sunday 22:00 UTC and closes Friday
22:00 UTC. Actual sessions shift with DST and vary by provider; therefore
weekend-model results must NEVER be treated as certified.
"""
from __future__ import annotations
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Iterable

STEP = {'M15': timedelta(minutes=15), 'H1': timedelta(hours=1)}

@dataclass(frozen=True)
class SessionAudit:
    timeframe: str
    observed: int
    expected: int
    missing: int
    unexpected: int
    duplicate: int
    missing_examples: tuple[str, ...]
    unexpected_examples: tuple[str, ...]
    status: str = 'weekend_model_only_not_certified'
    certified: bool = False

    def to_dict(self) -> dict:
        return asdict(self)


def _utc(value: Any) -> datetime:
    if isinstance(value, str):
        value = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise ValueError('Timestamps must be timezone-aware ISO strings or datetimes')
    return value.astimezone(timezone.utc)


def _assumed_open(start: datetime) -> bool:
    day = start.weekday()  # Monday=0, Sunday=6
    return day < 4 or (day == 4 and start.hour < 22) or (day == 6 and start.hour >= 22)


def audit_candles(candles: Iterable[Any], timeframe: str, *, max_examples: int = 5) -> SessionAudit:
    """Audit between first/last candle; cannot prove completeness outside that window."""
    if timeframe not in STEP:
        raise ValueError('Only H1 and M15 source candles are supported')
    if max_examples < 0:
        raise ValueError('max_examples must be nonnegative')
    step = STEP[timeframe]
    timestamps = []
    for candle in candles:
        value = candle.get('timestamp') if isinstance(candle, dict) else candle.timestamp
        timestamp = _utc(value)
        if timestamp.minute % (15 if timeframe == 'M15' else 60) != 0:
            raise ValueError('Candle timestamp is not timeframe aligned')
        if timestamp.second or timestamp.microsecond:
            raise ValueError('Candle timestamp is not timeframe aligned')
        timestamps.append(timestamp)
    if not timestamps:
        raise ValueError('No candles to audit')
    actual = set(timestamps)
    first, last = min(actual), max(actual)
    expected = set()
    cursor = first
    while cursor <= last:
        if _assumed_open(cursor):
            expected.add(cursor)
        cursor += step
    missing = sorted(expected - actual)
    unexpected = sorted(actual - expected)
    return SessionAudit(
        timeframe=timeframe, observed=len(timestamps), expected=len(expected),
        missing=len(missing), unexpected=len(unexpected),
        duplicate=len(timestamps) - len(actual),
        missing_examples=tuple(t.isoformat() for t in missing[:max_examples]),
        unexpected_examples=tuple(t.isoformat() for t in unexpected[:max_examples]),
    )
