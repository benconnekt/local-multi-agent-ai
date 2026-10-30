"""Explicit, versioned *provisional* OANDA holiday exceptions. No certification.

These intervals are derived from the user's observed OANDA historical feed gaps.
They MUST be cross-checked with an authoritative broker schedule before
being labelled verified. They never permit an unexpected candle or other gap.
"""
from dataclasses import dataclass
from datetime import datetime, timezone

UTC = timezone.utc

@dataclass(frozen=True)
class ClosureCalendar:
    calendar_id: str
    intervals: tuple[tuple[datetime, datetime], ...]
    verified: bool = False

    def is_closed(self, timestamp: datetime) -> bool:
        if timestamp.tzinfo is None:
            raise ValueError('Closure checks require aware UTC timestamps')
        ts = timestamp.astimezone(UTC)
        return any(start <= ts < end for start, end in self.intervals)


def _dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace('Z', '+00:00'))


OANDA_OBSERVED_2025_2026_V1 = ClosureCalendar(
    calendar_id='oanda_observed_holiday_gaps_2025_2026_v1_UNVERIFIED',
    intervals=(
        (_dt('2025-12-24T22:00:00Z'), _dt('2025-12-25T22:00:00Z')),
        (_dt('2025-12-31T22:00:00Z'), _dt('2026-01-01T22:00:00Z')),
    ),
)
