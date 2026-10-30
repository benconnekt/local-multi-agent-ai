"""Pure, fail-closed Forex historical candle validation.

All timestamps are UTC; ranges use [start, end). Weekend closure model is
Friday 22:00 UTC to Sunday 22:00 UTC, a configurable approximation rather
than an authoritative broker-specific trading calendar. Holidays and DST
must be addressed before certifying longer historical periods.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from math import isfinite
from typing import Mapping, Sequence

UTC = timezone.utc
MINUTES = {"M15": 15, "H1": 60, "H4": 240, "D1": 1440}


@dataclass(frozen=True)
class QualityReport:
    status: str
    expected: int
    observed: int
    missing: tuple[str, ...]
    unexpected: tuple[str, ...]
    issues: tuple[str, ...]
    calendar: str = "approx_forex_weekend_utc_22"

    @property
    def research_ready(self) -> bool:
        return self.status == "coverage_pass_weekend_model_only"


def parse_utc(value: str | datetime) -> datetime:
    dt = datetime.fromisoformat(value.replace("Z", "+00:00")) if isinstance(value, str) else value
    if dt.tzinfo is None or dt.utcoffset() != timedelta(0):
        raise ValueError("Timestamp must be explicitly UTC")
    return dt.astimezone(UTC)


def market_open(dt: datetime) -> bool:
    """Simplified FX week: Sun 22:00 UTC through Fri 22:00 UTC."""
    weekday = dt.weekday()
    return weekday < 4 or (weekday == 4 and dt.hour < 22) or (weekday == 6 and dt.hour >= 22)


def validate_candles(
    candles: Sequence[Mapping[str, object]],
    timeframe: str,
    start: str | datetime,
    end: str | datetime,
    *,
    max_missing_report: int = 100,
) -> QualityReport:
    if timeframe not in MINUTES:
        raise ValueError(f"Unsupported timeframe: {timeframe}")
    step = timedelta(minutes=MINUTES[timeframe])
    start_dt, end_dt = parse_utc(start), parse_utc(end)
    if start_dt >= end_dt:
        raise ValueError("Start must precede end")
    if any(dt.minute % MINUTES[timeframe] != 0 for dt in (start_dt, end_dt)) and timeframe in ("M15", "H1"):
        raise ValueError("Range must align with timeframe")
    if timeframe == "H4" and (start_dt.hour % 4 or end_dt.hour % 4 or start_dt.minute or end_dt.minute):
        raise ValueError("H4 range must align to UTC hours 00,04,08,12,16,20")
    if timeframe == "D1" and (start_dt.hour or end_dt.hour or start_dt.minute or end_dt.minute):
        raise ValueError("D1 range must align to midnight UTC")
    if (end_dt - start_dt).days > 366:
        raise ValueError("Validate at most 366 days per call")

    issues: list[str] = []
    observed: dict[datetime, Mapping[str, object]] = {}
    previous: datetime | None = None
    for index, candle in enumerate(candles):
        try:
            timestamp = parse_utc(candle["timestamp"])  # type: ignore[arg-type]
            values = {key: float(candle[key]) for key in ("open", "high", "low", "close")}
            if not all(isfinite(v) and v > 0 for v in values.values()):
                raise ValueError("non-finite or non-positive OHLC")
            if values["low"] > min(values["open"], values["close"]) or values["high"] < max(values["open"], values["close"]) or values["low"] > values["high"]:
                raise ValueError("inconsistent OHLC")
            if timestamp.minute % MINUTES[timeframe] != 0 or timestamp.second or timestamp.microsecond:
                raise ValueError("misaligned timestamp")
            if timeframe == "H4" and timestamp.hour % 4:
                raise ValueError("misaligned H4 timestamp")
            if timeframe == "D1" and timestamp.hour:
                raise ValueError("misaligned D1 timestamp")
            if previous is not None and timestamp <= previous:
                issues.append(f"Row {index}: out-of-order or duplicate timestamp")
            if timestamp in observed:
                issues.append(f"Row {index}: duplicate timestamp")
            observed[timestamp] = candle
            previous = timestamp
        except (ValueError, KeyError, TypeError, OverflowError) as exc:
            issues.append(f"Row {index}: {exc}")

    expected: set[datetime] = set()
    current = start_dt
    while current < end_dt:
        if market_open(current):
            expected.add(current)
        current += step
    missing_all = sorted(expected - observed.keys())
    unexpected_all = sorted(observed.keys() - expected)
    missing = tuple(dt.isoformat() for dt in missing_all[:max_missing_report])
    unexpected = tuple(dt.isoformat() for dt in unexpected_all[:max_missing_report])
    if issues or missing_all or unexpected_all:
        status = "failed"
    else:
        status = "coverage_pass_weekend_model_only"
    return QualityReport(status, len(expected), len(observed), missing, unexpected, tuple(issues))


def filter_date_range(candles: Sequence[Mapping[str, object]], start: str | datetime, end: str | datetime) -> list[Mapping[str, object]]:
    first, last = parse_utc(start), parse_utc(end)
    if first >= last:
        raise ValueError("Start must precede end")
    return [c for c in candles if first <= parse_utc(c["timestamp"]) < last]  # type: ignore[arg-type]


def aggregate_h1_to_h4(candles: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    """Only emit H4 buckets with exactly four consecutive, aligned H1 candles.

    A partial bucket raises rather than silently emitting an incomplete bar.
    """
    buckets: dict[datetime, list[Mapping[str, object]]] = {}
    for candle in candles:
        dt = parse_utc(candle["timestamp"])  # type: ignore[arg-type]
        if dt.minute or dt.second or dt.microsecond:
            raise ValueError("H1 candle timestamp must align to hour")
        bucket = dt.replace(hour=dt.hour // 4 * 4)
        buckets.setdefault(bucket, []).append(candle)
    output: list[dict[str, object]] = []
    for bucket, group in sorted(buckets.items()):
        ordered = sorted(group, key=lambda c: parse_utc(c["timestamp"]))  # type: ignore[arg-type]
        expected = [bucket + timedelta(hours=h) for h in range(4)]
        actual = [parse_utc(c["timestamp"]) for c in ordered]  # type: ignore[arg-type]
        if actual != expected:
            raise ValueError(f"Incomplete or duplicate H4 bucket at {bucket.isoformat()}")
        report = validate_candles(ordered, "H1", bucket, bucket + timedelta(hours=4))
        # A four-hour bucket can span market closure; reject any unexpected hours.
        if report.status != "coverage_pass_weekend_model_only":
            raise ValueError(f"Invalid H1 source bucket at {bucket.isoformat()}: {report.status}")
        output.append({
            "timestamp": bucket.isoformat(),
            "open": float(ordered[0]["open"]),
            "high": max(float(c["high"]) for c in ordered),
            "low": min(float(c["low"]) for c in ordered),
            "close": float(ordered[-1]["close"]),
            "volume": (
                sum(float(c["volume"]) for c in ordered)
                if all(c.get("volume") not in (None, "") for c in ordered)
                else None
            ),
        })
    return output
