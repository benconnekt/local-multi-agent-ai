"""Safe, read-only trading research diagnostics endpoints."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from app.trading.research.intelligence_lab import research_overview, indicator_evidence, ledger_diagnostics

router = APIRouter(prefix='/lab', tags=['forex-strategy-research'])
class EvidenceInput(BaseModel):
    closes: list[float] = Field(min_length=30, max_length=10000)
class LedgerInput(BaseModel):
    ledger: list[dict] = Field(max_length=10000)
    cost_r: float = Field(default=0.0, ge=0, le=5)
@router.get('/overview')
def overview(): return research_overview()
@router.post('/indicators')
def indicators(body: EvidenceInput):
    try: return indicator_evidence(body.closes)
    except ValueError as e: raise HTTPException(422,str(e)) from e
@router.post('/diagnostics')
def diagnostics(body: LedgerInput):
    try: return ledger_diagnostics(body.ledger,body.cost_r)
    except ValueError as e: raise HTTPException(422,str(e)) from e


# Offline historical research: reads existing imported CSV catalogue, never a broker.
from app.trading.research.historical_runner import run_historical_backtest
from app.trading.research.backtest_validation import audit_report
from pathlib import Path
from datetime import datetime
from math import isfinite

HISTORICAL_DIRECTORY = Path(__file__).resolve().parents[3] / 'data' / 'forex' / 'historical_real'

class HistoricalInput(BaseModel):
    instrument: str
    provider: str = 'oanda_v20'
    spread: float = Field(default=0.0, ge=0, le=0.1)
    slippage: float = Field(default=0.0, ge=0, le=0.1)

@router.get('/historical/datasets')
def historical_datasets():
    from app.trading.data.catalogue import discover
    try:
        entries = discover(HISTORICAL_DIRECTORY)
    except (ValueError, OSError) as exc:
        raise HTTPException(422, detail=f'Historical catalogue invalid: {exc}') from exc
    return {'datasets': [{'id': e['id'], 'instrument': e['instrument'], 'timeframe': e['timeframe'],
                          'source': e['source'], 'data_kind': e['data_kind']} for e in entries
                         if e.get('data_kind') == 'historical_real' and e.get('source') == 'oanda_v20'],
            'decision': 'NO_TRADE', 'research_only': True, 'independently_certified': False}

@router.post('/historical/backtest')
def historical_backtest(body: HistoricalInput):
    if body.instrument not in ('EURUSD','GBPUSD','USDJPY') or body.provider != 'oanda_v20':
        raise HTTPException(422, detail='Only supported OANDA research pairs are allowed')
    if not all(isfinite(v) for v in (body.spread, body.slippage)):
        raise HTTPException(422, detail='Costs must be finite')
    try:
        result = run_historical_backtest(HISTORICAL_DIRECTORY, body.instrument, provider=body.provider,
                                         spread=body.spread, slippage=body.slippage)
        audit = audit_report(result)
    except (ValueError, KeyError, OSError) as exc:
        raise HTTPException(422, detail=f'Historical research unavailable: {exc}') from exc
    # Return only bounded trade detail to protect browser responsiveness.
    return {'decision':'NO_TRADE', 'research_only':True, 'broker_execution_enabled':False,
            'independently_certified':False, 'quality_certified':False,
            'research_signal_eligible':False, 'instrument':body.instrument,
            'dataset_ids':result['dataset_ids'], 'generated_hypotheses':result['generated_hypotheses'],
            'simulated':result['simulated'], 'wins':result['wins'], 'losses':result['losses'],
            'unresolved':result['unresolved'], 'win_rate':result['win_rate'],
            'expectancy_r':result['expectancy_r'], 'total_r':result['total_r'],
            'max_drawdown_r':result['max_drawdown_r'], 'spread':result['spread'],
            'slippage':result['slippage'], 'audit':audit,
            'trades':result['trades'][:200], 'trades_truncated':len(result['trades'])>200,
            'warning':result['warning']}
