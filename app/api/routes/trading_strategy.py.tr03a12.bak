"""Read-only strategy readiness endpoint. Never authorises uncertified signals."""
from __future__ import annotations
from pathlib import Path
from typing import Annotated
from fastapi import APIRouter, Query
from app.trading.data.catalogue import discover
from app.trading.services.strategy_data_loader import DatasetNotReady, assemble
from app.trading.services.opportunity_evidence import unavailable_score
from app.trading.services.timeframe_readiness import inspect_timeframes
from app.trading.quality.readiness_report import build_session_readiness

router = APIRouter(prefix='/trading', tags=['trading-research'])
DATA_DIRECTORY = Path(__file__).resolve().parents[3] / 'data' / 'forex' / 'historical_real'

@router.get('/strategy/analyse')
def analyse(
    instrument: str = Query(pattern=r'^(EURUSD|GBPUSD|USDJPY)$'),
    provider: Annotated[
        str | None,
        Query(pattern=r'^(oanda_v20|yahoo_finance)$'),
    ] = None,
):
    entries = [d for d in discover(DATA_DIRECTORY)
               if d['instrument'] == instrument and d['data_kind'] == 'historical_real']
    providers = {d['source'] for d in entries}
    # Diagnostics and displayed provenance must describe the same provider scope.
    selected = [d for d in entries if d['source'] == provider] if provider is not None else entries
    ambiguous = provider is None and len(providers) > 1
    provenance = {
        d['id']: {'source': d['source'], 'timeframe': d['timeframe'],
                  'quality_status': d['quality_status'], 'count': d['count'],
                  'first_timestamp': d.get('first_timestamp'), 'last_timestamp': d['last_timestamp'],
                  'price_component': d.get('price_component'), 'environment': d.get('environment')}
        for d in selected
    }
    readiness = inspect_timeframes(entries, provider=provider)
    session_readiness = build_session_readiness(entries, provider=provider)
    try:
        assemble(DATA_DIRECTORY, instrument, provider=provider)
    except DatasetNotReady as exc:
        reason = str(exc)
    else:
        reason = 'Strategy evaluation requires independently certified FX market sessions'
    available = {d['timeframe'] for d in selected} if not ambiguous else set()
    missing = [tf for tf in ('H1', 'M15') if tf not in available]
    return {
        'instrument': instrument, 'provider': provider if provider is not None else (next(iter(providers)) if len(providers) == 1 else None),
        'available_providers': sorted(providers),
        'decision': 'NO_TRADE', 'reason': reason,
        'research_only': True, 'quality_certified': False,
        'datasets': provenance, 'missing_timeframes': missing,
        'entry': None, 'stop_loss': None, 'take_profit': None,
        'risk_fraction': 0.0, 'reward_to_risk': None,
        'indicators': None, 'as_of_utc': None,
        'opportunity_score': unavailable_score(reason),
        'timeframe_readiness': readiness,
        'session_readiness': session_readiness,
    }
