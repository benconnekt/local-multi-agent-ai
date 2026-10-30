"""Offline, read-only historical hypothesis evaluation. NEVER routes orders.

The provisional session audit is NOT independent data certification.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from app.trading.data.catalogue import discover
from app.trading.quality.fx_session_validation import audit_sessions
from app.trading.quality.holiday_calendar import OANDA_OBSERVED_2025_2026_V1
from app.trading.quality.broker_absences import BROKER_OBSERVED_ABSENCES_V1, EVIDENCE
from app.trading.research.backtest import Bar, simulate
from app.trading.research.hypothesis_generator import discover_hypotheses
from app.trading.research.session_policy import entry_allowed, evidence_fresh, is_weekend_hold

HOUR = timedelta(hours=1)
QUARTER = timedelta(minutes=15)
BASE = {'decision': 'NO_TRADE', 'research_only': True, 'quality_certified': False,
        'research_signal_eligible': False, 'hypothetical': True}


def _utc(value: Any) -> datetime:
    dt = value if isinstance(value, datetime) else datetime.fromisoformat(value.replace('Z', '+00:00'))
    if dt.tzinfo is None:
        raise ValueError('Naive historical timestamp')
    return dt.astimezone(timezone.utc)


def _bars(entries: list[dict], timeframe: str, *, provider: str = "oanda_v20", instrument: str = "") -> tuple[list[Bar], list[str]]:
    selected = [e for e in entries if e['timeframe'] == timeframe]
    if not selected:
        raise ValueError(f'Missing {timeframe} data')
    merged: dict[datetime, tuple] = {}
    for entry in selected:
        for candle in entry['candles']:
            row = candle.model_dump() if hasattr(candle, 'model_dump') else candle
            ts = _utc(row['timestamp'])
            signature = tuple(float(row[k]) for k in ('open', 'high', 'low', 'close')) + (
                None if row.get('volume') in (None, '') else float(row['volume']),)
            if ts in merged and merged[ts] != signature:
                raise ValueError(f'Conflicting {timeframe} overlap at {ts.isoformat()}')
            merged[ts] = signature
    ordered = [Bar(ts, *merged[ts][:4]) for ts in sorted(merged)]
    # Audit full OHLC, not only timestamps; duplicate overlaps were reconciled above.
    audit = audit_sessions([{'timestamp': b.timestamp, 'open': b.open, 'high': b.high,
                            'low': b.low, 'close': b.close} for b in ordered], timeframe,
                           calendar=OANDA_OBSERVED_2025_2026_V1 if provider == 'oanda_v20' else None,
                           acknowledged_absences=BROKER_OBSERVED_ABSENCES_V1.get((provider, instrument, timeframe), frozenset()))
    if not audit.provisional_schedule_pass:
        raise ValueError(f'{timeframe} provisional session audit failed: missing={audit.missing_expected_candles}, examples={list(audit.missing_examples)}, unexpected={audit.unexpected_session_candles}, duplicates={audit.duplicate_timestamps}, alignment={audit.misaligned_timestamps}, invalid_ohlc={audit.invalid_ohlc}; calendar={audit.calendar_id}; no synthetic candles permitted')
    return ordered, [e['id'] for e in selected]


def _continuous(rows: list[Bar], end: datetime, step: timedelta, count: int) -> bool:
    lookup = {b.timestamp for b in rows}
    return all(end - step * n in lookup for n in range(1, count + 1))


def run_historical_backtest(directory: Path, instrument: str, *, provider: str = 'oanda_v20',
                            as_of: datetime | None = None, spread: float = 0.0,
                            slippage: float = 0.0, risk_fraction: float = 0.005,
                            minimum_h4: int = 250) -> dict:
    """Offline research, never calls assemble(), strategy API, or broker adapters.

    Simulation is bounded to the next immediate M15 bar. A position remains
    active until its stop/target or the data ends; overlapping setups are skipped.
    """
    if instrument not in ('EURUSD', 'GBPUSD', 'USDJPY'):
        raise ValueError('Unsupported instrument')
    if provider not in ('oanda_v20', 'yahoo_finance'):
        raise ValueError('Explicit supported provider required')
    entries = [e for e in discover(directory) if e['instrument'] == instrument
               and e['data_kind'] == 'historical_real' and e['source'] == provider]
    if not entries:
        raise ValueError('No historical data for selected provider')
    h1, h1_ids = _bars(entries, 'H1', provider=provider, instrument=instrument)
    m15, m15_ids = _bars(entries, 'M15', provider=provider, instrument=instrument)
    cutoff = _utc(as_of) if as_of is not None else m15[-1].timestamp + QUARTER
    if cutoff > m15[-1].timestamp + QUARTER:
        raise ValueError('Evaluation timestamp exceeds last imported M15 close')
    if cutoff <= m15[0].timestamp:
        raise ValueError('No closed M15 history at evaluation timestamp')
    hypotheses = discover_hypotheses(h1, m15, as_of=cutoff, minimum_h4=minimum_h4)
    m15_index = {b.timestamp: i for i, b in enumerate(m15)}
    outcomes = []
    skipped = {'breakout_crosses_gap': 0, 'missing_immediate_entry': 0,
               'overlapping_position': 0, 'unresolved_position': 0,
               'entry_outside_policy': 0, 'stale_evidence': 0, 'weekend_holds': 0}
    occupied_until = None
    for candidate in hypotheses['hypotheses']:
        hypothesis = candidate['hypothesis']
        signal_time = _utc(hypothesis.signal_time)
        if not entry_allowed(signal_time):
            skipped['entry_outside_policy'] += 1
            continue
        if not evidence_fresh(candidate['evidence'], signal_time):
            skipped['stale_evidence'] += 1
            continue
        if occupied_until is not None and signal_time <= occupied_until:
            skipped['overlapping_position'] += 1
            continue
        # Last four M15 bars (3 breakout reference bars + signal) must be consecutive.
        if not _continuous(m15, signal_time, QUARTER, 4):
            skipped['breakout_crosses_gap'] += 1
            continue
        next_idx = m15_index.get(signal_time)
        if next_idx is None or signal_time + QUARTER > cutoff:
            skipped['missing_immediate_entry'] += 1
            continue
        if not entry_allowed(m15[next_idx].timestamp):
            skipped['entry_outside_policy'] += 1
            continue
        # Existing positions survive Friday and the weekend. Missing candles
        # represent a closed market, never synthetic weekend fills. The first
        # available reopening bar can gap through the stop; simulate() uses
        # the worse reopening open for a stop and never improves target fills.
        future = [bar for bar in m15[next_idx:] if bar.timestamp + QUARTER <= cutoff]
        if not future:
            skipped['missing_immediate_entry'] += 1
            continue
        outcome = simulate(future, hypothesis, spread=spread, slippage=slippage,
                           risk_fraction=risk_fraction)
        last_time = (_utc(outcome['exit_time_utc']) if outcome.get('exit_time_utc')
                     else future[-1].timestamp + QUARTER)
        if is_weekend_hold(signal_time, last_time):
            skipped['weekend_holds'] += 1
        if outcome['outcome'] == 'unresolved':
            skipped['unresolved_position'] += 1
            occupied_until = future[-1].timestamp + QUARTER
        else:
            occupied_until = _utc(outcome['exit_time_utc']) if outcome.get('exit_time_utc') else signal_time
        outcomes.append({'signal_time_utc': signal_time.isoformat(),
                         'direction': hypothesis.direction, 'evidence': candidate['evidence'],
                         'simulation': outcome})
    resolved = [x['simulation']['r_multiple'] for x in outcomes
                if x['simulation']['outcome'] in ('win', 'loss')]
    wins = sum(x['simulation']['outcome'] == 'win' for x in outcomes)
    losses = sum(x['simulation']['outcome'] == 'loss' for x in outcomes)
    equity = peak = drawdown = 0.0
    for r in resolved:
        equity += r
        peak = max(peak, equity)
        drawdown = max(drawdown, peak - equity)
    return {**BASE, 'instrument': instrument, 'provider': provider,
            'as_of_utc': cutoff.isoformat(), 'evaluation_basis': 'imported_history_only',
            'provisional_session_audit': True, 'independently_certified': False,
            'holiday_calendar_id': OANDA_OBSERVED_2025_2026_V1.calendar_id if provider == 'oanda_v20' else None,
            'holiday_calendar_verified': False,
            'broker_observed_absences': ([EVIDENCE] if (provider, instrument, 'M15') in BROKER_OBSERVED_ABSENCES_V1 else []),
            'broker_absence_policy': 'No synthetic candles; nonconsecutive breakout windows rejected',
            'dataset_ids': {'H1': h1_ids, 'M15': m15_ids},
            'evaluated_m15_candles': hypotheses['evaluated_m15_candles'],
            'generated_hypotheses': len(hypotheses['hypotheses']),
            'rejected_counts': hypotheses['rejected_counts'], 'skipped_counts': skipped,
            'simulated': len(outcomes), 'wins': wins, 'losses': losses,
            'unresolved': sum(x['simulation']['outcome'] == 'unresolved' for x in outcomes),
            'weekend_holds': skipped['weekend_holds'],
            'session_policy': 'NY entry window Monday 01:00 through Friday before 16:00; existing positions held across weekends',
            'win_rate': wins / (wins + losses) if wins + losses else None,
            'expectancy_r': sum(resolved) / len(resolved) if resolved else None,
            'total_r': sum(resolved), 'max_drawdown_r': drawdown,
            'spread': spread, 'slippage': slippage, 'risk_fraction': risk_fraction,
            'trades': outcomes,
            'warning': 'Uncertified historical simulation; holiday exceptions based on observed gaps and NOT independently verified; no broker execution or live signal eligibility'}
