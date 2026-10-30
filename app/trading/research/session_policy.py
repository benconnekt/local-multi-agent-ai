"""Conservative NY-local Forex entry and weekend holding policy; research only."""
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

NY = ZoneInfo('America/New_York')
QUARTER = timedelta(minutes=15)
HOUR = timedelta(hours=1)

def utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise ValueError('Timezone-aware timestamp required')
    return value.astimezone(timezone.utc)

def entry_allowed(value: datetime) -> bool:
    """Friday <16:00; no Sat/Sun; Monday >=01:00, New York local."""
    local = utc(value).astimezone(NY)
    day = local.weekday()
    minute = local.hour * 60 + local.minute
    return (day in (1, 2, 3) or (day == 0 and minute >= 60)
            or (day == 4 and minute < 16 * 60))

def market_open_hour_count(start: datetime, end: datetime) -> int:
    """Count provisionally expected hourly slots; no independent certification."""
    from app.trading.quality.fx_session_validation import _market_open
    cursor = utc(start)
    stop = utc(end)
    if stop < cursor:
        raise ValueError('Future evidence timestamp')
    if (stop - cursor) > timedelta(days=30):
        raise ValueError('Unbounded freshness interval')
    count = 0
    while cursor < stop:
        if _market_open(cursor):
            count += 1
        cursor += HOUR
    return count

def evidence_fresh(evidence: dict, signal_time: datetime) -> bool:
    signal = utc(signal_time)
    for key, allowed in [('h4_last_close_utc', 4), ('h1_last_close_utc', 1)]:
        close = datetime.fromisoformat(evidence[key].replace('Z', '+00:00'))
        if market_open_hour_count(close, signal) > allowed:
            return False
    return True

def is_weekend_hold(start: datetime, end: datetime) -> bool:
    """True if a position interval crosses a Friday 16:00 NY entry cutoff.

    Diagnostic only: never liquidates or authorises an order.
    """
    first, last = utc(start), utc(end)
    if last < first:
        raise ValueError('Invalid position interval')
    cursor = first.astimezone(NY).date()
    while cursor <= last.astimezone(NY).date():
        if cursor.weekday() == 4:
            boundary = datetime(cursor.year, cursor.month, cursor.day, 16, tzinfo=NY).astimezone(timezone.utc)
            if first < boundary <= last:
                return True
        cursor += timedelta(days=1)
    return False
