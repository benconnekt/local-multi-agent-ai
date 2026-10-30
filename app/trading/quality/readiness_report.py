"""Provider-scoped, overlap-aware diagnostics; never certifies trading readiness."""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Any
from app.trading.quality.fx_session_validation import audit_sessions, derive_h4_summary
from app.trading.quality.h4_integrity import analyse_h4


def _utc(value: Any) -> datetime:
    dt = value if isinstance(value, datetime) else datetime.fromisoformat(value.replace('Z', '+00:00'))
    if dt.tzinfo is None:
        raise ValueError('Naive timestamp')
    return dt.astimezone(timezone.utc)


def _reconcile(items: list[dict], timeframe: str) -> tuple[list[Any], int]:
    """Reconcile identical overlap; report conflicts without selecting a winner."""
    merged: dict[datetime, Any] = {}
    values: dict[datetime, tuple] = {}
    conflicts = 0
    for item in items:
        if item.get('timeframe') != timeframe:
            continue
        for candle in item.get('candles', []):
            row = candle.model_dump() if hasattr(candle, 'model_dump') else candle
            ts = _utc(row['timestamp'])
            signature = tuple(float(row[k]) for k in ('open', 'high', 'low', 'close')) + (None if row.get('volume') in (None, '') else float(row['volume']),)
            if ts in values and values[ts] != signature:
                conflicts += 1
            else:
                values[ts] = signature
                merged[ts] = candle
    if conflicts:
        return [], conflicts  # no ambiguous candles enter session or H4 diagnostics
    return [merged[t] for t in sorted(merged)], 0


def build_session_readiness(entries: list[dict[str, Any]], *, provider: str | None = None) -> dict[str, Any]:
    sources = {item.get('source') for item in entries if item.get('timeframe') in ('H1', 'M15')}
    if provider is not None:
        if provider not in ('oanda_v20', 'yahoo_finance'):
            raise ValueError('Unsupported historical provider')
        selected = [item for item in entries if item.get('source') == provider]
    elif len(sources) == 1:
        provider = next(iter(sources))
        selected = entries
    else:
        return {'H1': None, 'M15': None, 'H4': None,
                'provider': None, 'status': 'provider_selection_required',
                'certification_status': 'pending_independent_provider_calendar_and_data_verification',
                'research_signal_eligible': False}
    result: dict[str, Any] = {'provider': provider}
    h1: list[Any] = []
    for tf in ('H1', 'M15'):
        rows, conflicts = _reconcile(selected, tf)
        if conflicts:
            result[tf] = {'timeframe': tf, 'status': 'conflicting_overlaps',
                          'conflict_count': conflicts, 'independently_certified': False}
        else:
            result[tf] = audit_sessions(rows, tf).to_dict()
        if tf == 'H1':
            h1 = rows
    if result['H1'].get('status') == 'conflicting_overlaps':
        result['H4'] = {
            'source': 'derived_from_H1', 'status': 'invalid_source',
            'reason': 'Conflicting H1 overlaps; H4 derivation prohibited',
            'complete_candles': 0, 'incomplete_groups': 0,
            'independently_certified': False,
        }
    else:
        result['H4'] = derive_h4_summary(h1)
        result['H4']['integrity'] = analyse_h4(h1)
    result['certification_status'] = 'pending_independent_provider_calendar_and_data_verification'
    result['research_signal_eligible'] = False
    return result
