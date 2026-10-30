"""Fail-closed historical assembly; provider selection is not certification."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from app.trading.data.catalogue import discover
from app.trading.quality.fx_session_validation import audit_sessions

UTC = timezone.utc
STEP = {'M15': timedelta(minutes=15), 'H1': timedelta(hours=1)}
PROVIDERS = ('oanda_v20', 'yahoo_finance')

class DatasetNotReady(ValueError):
    """Historical data is not eligible for strategy evaluation."""

@dataclass(frozen=True)
class AssembledData:
    h4: list[dict[str, Any]]
    h1: list[dict[str, Any]]
    m15: list[dict[str, Any]]
    as_of: datetime
    provenance: dict[str, list[str]]

def _utc(value: Any) -> datetime:
    if isinstance(value, datetime):
        dt = value
    elif isinstance(value, str):
        dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
    else:
        raise DatasetNotReady('Invalid timestamp')
    if dt.tzinfo is None:
        raise DatasetNotReady('Naive timestamp')
    return dt.astimezone(UTC)

def _row(candle: Any) -> dict[str, Any]:
    if hasattr(candle, 'model_dump'):
        candle = candle.model_dump()
    return {'timestamp': _utc(candle['timestamp']).isoformat(),
            'open': float(candle['open']), 'high': float(candle['high']),
            'low': float(candle['low']), 'close': float(candle['close']),
            'volume': None if candle.get('volume') in (None, '') else float(candle['volume'])}

def _merge(entries: list[dict], timeframe: str, cutoff: datetime) -> tuple[list[dict], list[str]]:
    selected = [d for d in entries if d['timeframe'] == timeframe]
    if not selected:
        raise DatasetNotReady(f'Missing {timeframe} historical datasets')
    merged: dict[datetime, dict] = {}
    used: list[str] = []
    for item in selected:
        used.append(item['id'])
        for candle in item['candles']:
            row = _row(candle)
            timestamp = _utc(row['timestamp'])
            if timestamp + STEP[timeframe] > cutoff:
                continue
            if timestamp in merged and merged[timestamp] != row:
                raise DatasetNotReady(f'Conflicting overlapping {timeframe} candles at {timestamp.isoformat()}')
            merged[timestamp] = row
    ordered = [merged[t] for t in sorted(merged)]
    if not ordered:
        raise DatasetNotReady(f'No closed {timeframe} candles')
    return ordered, used

def _check_contiguous(rows: list[dict], timeframe: str) -> None:
    """Require complete provisional in-session coverage; never certify data."""
    try:
        audit = audit_sessions(rows, timeframe)
    except (ValueError, TypeError, KeyError, OverflowError) as exc:
        raise DatasetNotReady(
            f'{timeframe} invalid session data: {exc}'
        ) from exc

    if not audit.provisional_schedule_pass:
        issues = []
        for field in (
            'missing_expected_candles',
            'unexpected_session_candles',
            'duplicate_timestamps',
            'misaligned_timestamps',
            'invalid_ohlc',
        ):
            count = getattr(audit, field)
            if count:
                issues.append(f'{field}={count}')

        raise DatasetNotReady(
            f'{timeframe} historical gap or session validation failed: '
            + (', '.join(issues) if issues else 'no eligible candles')
            + '; not certified'
        )

def _h4_from_h1(rows: list[dict]) -> list[dict]:
    groups: dict[datetime, list[dict]] = {}
    for row in rows:
        ts = _utc(row['timestamp'])
        bucket = ts.replace(hour=(ts.hour // 4) * 4, minute=0, second=0, microsecond=0)
        groups.setdefault(bucket, []).append(row)
    output: list[dict] = []
    for bucket, group in sorted(groups.items()):
        if len(group) != 4 or any(_utc(r['timestamp']) != bucket + timedelta(hours=i) for i, r in enumerate(group)):
            continue
        output.append({'timestamp': bucket.isoformat(), 'open': group[0]['open'],
                       'high': max(r['high'] for r in group), 'low': min(r['low'] for r in group),
                       'close': group[-1]['close'],
                       'volume': sum(r['volume'] for r in group) if all(r['volume'] is not None for r in group) else None})
    return output

def assemble(directory: Path, instrument: str, *, as_of: datetime | str | None = None,
             provider: str | None = None) -> AssembledData:
    if instrument not in ('EURUSD', 'GBPUSD', 'USDJPY'):
        raise DatasetNotReady('Unsupported instrument')
    if provider is not None and provider not in PROVIDERS:
        raise DatasetNotReady('Unsupported historical provider')
    entries = [d for d in discover(directory) if d['instrument'] == instrument and d['data_kind'] == 'historical_real']
    if not entries:
        raise DatasetNotReady('No verified historical datasets')
    providers = {d['source'] for d in entries}
    if provider is None:
        if len(providers) != 1:
            raise DatasetNotReady('Multiple historical providers found; explicit provider selection required')
        provider = next(iter(providers))
    entries = [d for d in entries if d['source'] == provider]
    if not entries:
        raise DatasetNotReady(f'No historical datasets for selected provider: {provider}')
    cutoff = _utc(as_of) if as_of is not None else datetime.now(UTC)
    h1, h1_ids = _merge(entries, 'H1', cutoff)
    m15, m15_ids = _merge(entries, 'M15', cutoff)
    _check_contiguous(h1, 'H1')
    _check_contiguous(m15, 'M15')
    h4 = _h4_from_h1(h1)
    if len(h4) < 200 or len(h1) < 200 or len(m15) < 16:
        raise DatasetNotReady('Insufficient aligned history for H4 EMA 200 and lower timeframes')
    evaluation = min(cutoff, _utc(m15[-1]['timestamp']) + STEP['M15'])
    evaluation = evaluation.replace(second=0, microsecond=0)
    if evaluation.minute % 15:
        raise DatasetNotReady('Evaluation timestamp not M15 aligned')
    if evaluation - (_utc(h1[-1]['timestamp']) + STEP['H1']) > timedelta(hours=1):
        raise DatasetNotReady('Stale H1 data')
    if evaluation - (_utc(h4[-1]['timestamp']) + timedelta(hours=4)) > timedelta(hours=4):
        raise DatasetNotReady('Stale H4 data')
    raise DatasetNotReady('Market-session calendar certification is pending; research signals disabled')
