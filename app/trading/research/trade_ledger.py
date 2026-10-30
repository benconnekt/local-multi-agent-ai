"""Additive, offline trade-ledger audit. Never authorises or routes orders."""
from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
from math import isclose, isfinite
from pathlib import Path
from typing import Any

from app.trading.research.backtest_validation import audit_report
from app.trading.research.session_policy import entry_allowed, evidence_fresh, is_weekend_hold

SAFETY = {'decision': 'NO_TRADE', 'research_only': True, 'quality_certified': False,
          'research_signal_eligible': False, 'independently_certified': False,
          'hypothetical': True}


def _time(value: str) -> datetime:
    dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if dt.tzinfo is None:
        raise ValueError('Naive timestamp in trade ledger')
    return dt.astimezone(timezone.utc)


def _finite_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and isfinite(value)


def build_trade_ledger(report: dict[str, Any]) -> dict[str, Any]:
    """Audit an existing backtest report without changing its trade population."""
    if any(report.get(key) != value for key, value in SAFETY.items()):
        raise ValueError('Unsafe or incomplete research safety flags')
    baseline = audit_report(report)
    failures = list(baseline['failures'])
    warnings = list(baseline['warnings'])
    ledger = []
    previous_exit = None
    for index, trade in enumerate(report['trades']):
        sim = trade['simulation']
        signal = _time(trade['signal_time_utc'])
        outcome = sim['outcome']
        entry = _time(sim['entry_time_utc']) if sim.get('entry_time_utc') else None
        exit_ = _time(sim['exit_time_utc']) if sim.get('exit_time_utc') else None
        if not entry_allowed(signal) or (entry is not None and not entry_allowed(entry)):
            failures.append({'trade': index, 'code': 'entry_outside_session_policy'})
        try:
            if not evidence_fresh(trade['evidence'], signal):
                failures.append({'trade': index, 'code': 'stale_session_evidence'})
        except (KeyError, TypeError, ValueError) as exc:
            failures.append({'trade': index, 'code': 'invalid_evidence', 'detail': str(exc)})
        if entry is not None and entry != signal:
            failures.append({'trade': index, 'code': 'entry_not_immediate_next_bar'})
        if previous_exit is not None and signal <= previous_exit:
            failures.append({'trade': index, 'code': 'overlapping_trade'})
        if outcome in ('win', 'loss'):
            if exit_ is None or entry is None:
                failures.append({'trade': index, 'code': 'missing_fill_timestamp'})
            else:
                previous_exit = exit_
            direction = trade.get('direction')
            side = 1 if direction == 'LONG' else -1 if direction == 'SHORT' else 0
            if not side:
                failures.append({'trade': index, 'code': 'invalid_direction'})
            required = ('entry', 'exit', 'stop', 'target', 'r_multiple')
            if any(not _finite_number(sim.get(key)) for key in required):
                failures.append({'trade': index, 'code': 'invalid_execution_price_or_r'})
            else:
                distance = side * (sim['entry'] - sim['stop'])
                if distance <= 0:
                    failures.append({'trade': index, 'code': 'invalid_stop_direction'})
                else:
                    calculated = side * (sim['exit'] - sim['entry']) / distance
                    if not isclose(calculated, sim['r_multiple'], abs_tol=1e-8, rel_tol=1e-8):
                        failures.append({'trade': index, 'code': 'execution_r_mismatch', 'calculated': calculated})
                    if side * (sim['target'] - sim['entry']) / distance < 2 - 1e-8:
                        failures.append({'trade': index, 'code': 'reward_risk_below_minimum'})
        elif outcome == 'unresolved':
            # The report does not contain the last available candle/mark-to-market.
            previous_exit = _time(report['as_of_utc'])
            warnings.append({'trade': index, 'code': 'unresolved_mark_to_market_unavailable'})
        else:
            failures.append({'trade': index, 'code': 'unsupported_trade_outcome'})
        if entry is not None and exit_ is not None:
            crossed = is_weekend_hold(entry, exit_)
        elif entry is not None and outcome == 'unresolved':
            crossed = is_weekend_hold(entry, _time(report['as_of_utc']))
        else:
            crossed = None
        ledger.append({
            'index': index, 'signal_time_utc': signal.isoformat(),
            'entry_time_utc': entry.isoformat() if entry else None,
            'exit_time_utc': exit_.isoformat() if exit_ else None,
            'direction': trade.get('direction'), 'outcome': outcome,
            'entry': sim.get('entry'), 'stop': sim.get('stop'),
            'target': sim.get('target'), 'exit': sim.get('exit'),
            'r_multiple': sim.get('r_multiple'),
            'ambiguity_stop_first': sim.get('ambiguity_stop_first'),
            'weekend_hold': crossed, 'evidence': trade.get('evidence'),
        })
    counted_holds = sum(row['weekend_hold'] is True for row in ledger)
    if report.get('weekend_holds') != counted_holds:
        failures.append({'code': 'weekend_hold_count_mismatch', 'expected': counted_holds,
                         'reported': report.get('weekend_holds')})
    if sum(report.get('skipped_counts', {}).get(k, 0) for k in
           ('entry_outside_policy', 'stale_evidence', 'overlapping_position',
            'breakout_crosses_gap', 'missing_immediate_entry')) + len(ledger) != report.get('generated_hypotheses'):
        failures.append({'code': 'hypothesis_accounting_mismatch'})
    metadata = {key: report.get(key) for key in ('instrument', 'provider', 'as_of_utc',
                'dataset_ids', 'spread', 'slippage', 'risk_fraction', 'session_policy',
                'generated_hypotheses', 'simulated')}
    digest = sha256(json.dumps({'metadata': metadata, 'ledger': ledger},
                                sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()
    return {**SAFETY, 'metadata': metadata, 'ledger': ledger,
            'ledger_sha256': digest, 'audit_pass': not failures,
            'failures': failures, 'warnings': warnings,
            'reconciled': baseline['reconciled'],
            'limitations': [*baseline['limitations'],
                'No independently verified tick/bid-ask fills or weekend liquidity',
                'Rejected hypotheses are aggregate counts, not individual records',
                'Unresolved positions lack a final mark-to-market price']}


def export_trade_ledger(report: dict[str, Any], destination: Path) -> dict[str, Any]:
    result = build_trade_ledger(report)
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + '\n', encoding='utf-8')
    return result
