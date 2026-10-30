"""Fail-closed, offline diagnostics for TR-03A.14 historical research reports.

Does not certify data, generate signals, or route orders.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from math import isclose, isfinite
from pathlib import Path
from typing import Any

from app.trading.research.historical_runner import run_historical_backtest

M15 = timedelta(minutes=15)
H1 = timedelta(hours=1)
H4 = timedelta(hours=4)
SAFE = {'decision': 'NO_TRADE', 'research_only': True, 'quality_certified': False,
        'research_signal_eligible': False, 'hypothetical': True, 'independently_certified': False}


def _time(value: str) -> datetime:
    result = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if result.tzinfo is None:
        raise ValueError('Naive audit timestamp')
    return result.astimezone(timezone.utc)


def audit_report(report: dict[str, Any]) -> dict[str, Any]:
    """Independently reconcile trade counts, R and drawdown; flag weak evidence.

    Freshness here checks evidence timestamps against each signal, NOT provider
    session certification or whether the last H1/H4 candle should exist.
    """
    if report.get('decision') != 'NO_TRADE' or report.get('research_only') is not True or report.get('quality_certified') is not False:
        raise ValueError('Unsafe or non-research backtest report')
    trades = report.get('trades')
    if not isinstance(trades, list):
        raise ValueError('Missing trade-level audit records')
    failures: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    resolved: list[float] = []
    wins = losses = unresolved = 0
    equity = peak = drawdown = 0.0
    for index, trade in enumerate(trades):
        sim = trade['simulation']
        signal = _time(trade['signal_time_utc'])
        evidence = trade['evidence']
        for key, period in (('h1_last_close_utc', H1), ('h4_last_close_utc', H4)):
            last = _time(evidence[key])
            age = signal - last
            if age < timedelta(0):
                failures.append({'trade': index, 'code': f'future_{key}'})
            elif age > period:
                warnings.append({'trade': index, 'code': f'stale_{key}', 'age_minutes': age.total_seconds() / 60})
        if _time(evidence['signal_close_utc']) != signal:
            failures.append({'trade': index, 'code': 'signal_evidence_mismatch'})
        outcome = sim['outcome']
        if outcome in ('win', 'loss'):
            if 'entry_time_utc' not in sim or 'exit_time_utc' not in sim:
                failures.append({'trade': index, 'code': 'missing_execution_times'})
            else:
                entry = _time(sim['entry_time_utc'])
                exit_ = _time(sim['exit_time_utc'])
                if entry != signal or exit_ < entry:
                    failures.append({'trade': index, 'code': 'invalid_execution_chronology'})
            r = sim.get('r_multiple')
            if not isinstance(r, (float, int)) or not isfinite(r):
                failures.append({'trade': index, 'code': 'invalid_r_multiple'})
                continue
            if outcome == 'win' and r <= 0 or outcome == 'loss' and r >= 0:
                failures.append({'trade': index, 'code': 'outcome_r_disagreement'})
            resolved.append(float(r))
            wins += outcome == 'win'
            losses += outcome == 'loss'
            equity += r
            peak = max(peak, equity)
            drawdown = max(drawdown, peak - equity)
        elif outcome == 'unresolved':
            unresolved += 1
            if sim.get('r_multiple') is not None:
                failures.append({'trade': index, 'code': 'unresolved_has_realized_r'})
        else:
            failures.append({'trade': index, 'code': 'unsupported_outcome'})
    expected = {'simulated': len(trades), 'wins': wins, 'losses': losses,
                'unresolved': unresolved}
    for key, value in expected.items():
        if report.get(key) != value:
            failures.append({'code': f'{key}_mismatch', 'expected': value, 'reported': report.get(key)})
    metrics = {'total_r': sum(resolved), 'expectancy_r': sum(resolved) / len(resolved) if resolved else None,
               'win_rate': wins / len(resolved) if resolved else None, 'max_drawdown_r': drawdown}
    for key, value in metrics.items():
        actual = report.get(key)
        if (value is None and actual is not None) or (value is not None and
            (not isinstance(actual, (int, float)) or not isfinite(actual) or not isclose(value, actual, abs_tol=1e-9, rel_tol=1e-9))):
            failures.append({'code': f'{key}_mismatch', 'expected': value, 'reported': actual})
    if unresolved:
        warnings.append({'code': 'unresolved_excluded_from_realized_performance', 'count': unresolved})
    if len(resolved) < 100:
        warnings.append({'code': 'small_resolved_sample', 'count': len(resolved)})
    if report.get('spread', 0) == 0:
        warnings.append({'code': 'zero_spread_assumption'})
    if report.get('slippage', 0) == 0:
        warnings.append({'code': 'zero_slippage_assumption'})
    return {**SAFE, 'instrument': report.get('instrument'), 'provider': report.get('provider'),
            'audit_pass': not failures, 'failures': failures, 'warnings': warnings,
            'reconciled': {**expected, **metrics},
            'limitations': ['Session calendar and H4 conventions not independently certified',
                            'H1/H4 age is a diagnostic; no session-aware freshness exception',
                            'No intrabar spread path, financing, or variable liquidity modelling',
                            'Unresolved trades are excluded from realized expectancy']}


def run_cost_sensitivity(directory: Path, instrument: str, *, provider: str = 'oanda_v20',
                         spreads: tuple[float, ...], slippages: tuple[float, ...] = (0.0,),
                         as_of: datetime | None = None) -> dict[str, Any]:
    """Re-run unchanged strategy at explicitly supplied, non-negative costs."""
    if not spreads or not slippages or len(spreads) * len(slippages) > 25:
        raise ValueError('Supply 1-25 cost scenarios')
    if any(not isinstance(x, (int, float)) or not isfinite(x) or x < 0 for x in (*spreads, *slippages)):
        raise ValueError('Invalid execution cost')
    scenarios = []
    for spread in spreads:
        for slippage in slippages:
            report = run_historical_backtest(directory, instrument, provider=provider,
                                             as_of=as_of, spread=spread, slippage=slippage)
            audit = audit_report(report)
            scenarios.append({'spread': spread, 'slippage': slippage,
                              'generated_hypotheses': report['generated_hypotheses'],
                              'simulated': report['simulated'], 'wins': report['wins'],
                              'losses': report['losses'], 'unresolved': report['unresolved'],
                              'expectancy_r': report['expectancy_r'], 'total_r': report['total_r'],
                              'max_drawdown_r': report['max_drawdown_r'],
                              'audit_pass': audit['audit_pass'], 'failures': audit['failures'],
                              'warnings': audit['warnings']})
    return {**SAFE, 'instrument': instrument, 'provider': provider, 'scenarios': scenarios,
            'warning': 'Research-only cost sensitivity; not independent market-data certification'}
