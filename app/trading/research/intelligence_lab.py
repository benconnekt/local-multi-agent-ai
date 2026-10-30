"""TR-05 research-only workbench: auditable evidence, no execution or auto-promotion."""
from __future__ import annotations
from hashlib import sha256
import json
from math import isfinite
from statistics import mean
from typing import Any

PAIRS = ('EURUSD', 'GBPUSD', 'USDJPY')
SAFETY = dict(decision='NO_TRADE', research_only=True, broker_execution_enabled=False,
              quality_certified=False, research_signal_eligible=False,
              independently_certified=False)
STRATEGIES = (
    dict(id='baseline_breakout', version='frozen-v1', status='baseline_pending_audit', description='Existing deterministic historical hypothesis engine'),
    dict(id='trend_pullback', version='proposal-v0', status='not_implemented', description='Proposed; no tested edge'),
    dict(id='breakout_retest', version='proposal-v0', status='not_implemented', description='Proposed; no tested edge'),
    dict(id='liquidity_sweep', version='proposal-v0', status='not_implemented', description='Proposed; no tested edge'),
)

def research_overview() -> dict[str, Any]:
    return {**SAFETY, 'pairs': list(PAIRS), 'strategies': list(STRATEGIES),
            'workstreams': {
                'TR-05.1': 'baseline_audit_available_on_uploaded_ledger',
                'TR-05.2': 'deterministic_indicator_evidence_available',
                'TR-05.3': 'versioned_proposal_registry_no_execution',
                'TR-05.4': 'cost_sensitivity_diagnostic_not_true_walk_forward',
                'TR-05.5': 'feedback_diagnostics_no_self_training',
                'TR-05.6': 'forward_protocol_defined_not_running'},
            'validation_pass': False,
            'limitations': ['No independently certified data', 'No unseen forward validation',
                            'No demonstrated net profitable strategy']}

def indicator_evidence(closes: list[float]) -> dict[str, Any]:
    if len(closes) < 30 or len(closes) > 10000 or any(not isfinite(v) or v <= 0 for v in closes):
        raise ValueError('Supply 30–10000 finite positive historical closes')
    fast = mean(closes[-10:]); slow = mean(closes[-30:])
    changes = [b-a for a,b in zip(closes[-15:-1], closes[-14:])]
    gains = sum(max(x,0) for x in changes); losses = sum(max(-x,0) for x in changes)
    rsi = 100.0 if losses == 0 and gains > 0 else 50.0 if losses == gains == 0 else 100 - 100/(1+gains/losses)
    return {**SAFETY, 'observations': len(closes), 'sma_10': round(fast, 8),
            'sma_30': round(slow, 8), 'rsi_14': round(rsi, 3),
            'trend_observation': 'above_sma30' if closes[-1] > slow else 'below_sma30' if closes[-1] < slow else 'at_sma30',
            'limitations': ['Close-only evidence; not ATR, swing structure, spread, or a trading signal']}

def ledger_diagnostics(ledger: list[dict[str, Any]], cost_r: float = 0.0) -> dict[str, Any]:
    if len(ledger) > 10000 or not isfinite(cost_r) or not 0 <= cost_r <= 5:
        raise ValueError('Invalid ledger size or cost_r')
    values: list[float] = []; wins = 0; losses = 0; unresolved = 0
    previous = None
    for item in ledger:
        if not isinstance(item, dict) or item.get('outcome') not in ('win','loss','unresolved'):
            raise ValueError('Invalid ledger outcome')
        timestamp = item.get('signal_time_utc')
        if not isinstance(timestamp,str) or not timestamp.endswith('Z') or (previous is not None and timestamp <= previous):
            raise ValueError('Ledger must be strictly chronological with UTC Z timestamps')
        previous = timestamp
        if item['outcome'] == 'unresolved':
            if item.get('r_multiple') is not None: raise ValueError('Unresolved trade cannot have realised R')
            unresolved += 1; continue
        r = item.get('r_multiple')
        if isinstance(r,bool) or not isinstance(r,(int,float)) or not isfinite(r): raise ValueError('Invalid realised R')
        if item['outcome'] == 'win' and r <= 0 or item['outcome'] == 'loss' and r >= 0:
            raise ValueError('Outcome and realised R disagree')
        values.append(float(r)-cost_r)
        wins += item['outcome']=='win'; losses += item['outcome']=='loss'
    equity=peak=drawdown=0.0
    for r in values:
        equity += r; peak=max(peak,equity); drawdown=max(drawdown,peak-equity)
    positive=sum(v for v in values if v>0); negative=-sum(v for v in values if v<0)
    digest=sha256(json.dumps(ledger,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    return {**SAFETY, 'hypothetical': True, 'ledger_sha256': digest, 'resolved':len(values),
            'wins':wins,'losses':losses,'unresolved':unresolved,'cost_r_per_resolved_trade':cost_r,
            'win_rate':wins/len(values) if values else None,
            'net_expectancy_r':mean(values) if values else None,
            'net_total_r':sum(values), 'max_drawdown_r':drawdown,
            'profit_factor':positive/negative if negative>0 else None,
            'profit_factor_note':'undefined_without_losses' if negative==0 else None,
            'sample_sufficient':len(values)>=100, 'validation_pass':False,
            'learning_feedback': ['Collect more resolved observations before drawing conclusions'] if len(values)<100 else
                ['Review stability by pair, regime, and time window; no automatic strategy promotion'],
            'limitations':['Retrospective cohort; not unseen data', 'Cost R is a sensitivity assumption, not observed bid/ask costs',
                           'No independent certification or live trading eligibility']}
