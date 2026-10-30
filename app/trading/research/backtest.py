"""Research-only deterministic OHLC exit simulator. No broker or signal integration."""
from __future__ import annotations
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Iterable
import math

@dataclass(frozen=True)
class Bar:
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float

@dataclass(frozen=True)
class Hypothesis:
    direction: str  # LONG or SHORT
    signal_time: datetime  # completed signal candle's CLOSE timestamp
    stop_distance: float
    reward_to_risk: float = 2.0


def _utc(t: datetime) -> datetime:
    if t.tzinfo is None:
        raise ValueError('Timezone-aware timestamps required')
    return t.astimezone(timezone.utc)


def simulate(bars: Iterable[Bar], hypothesis: Hypothesis, *, spread: float = 0.0,
             slippage: float = 0.0, risk_fraction: float = 0.005) -> dict:
    """Next-bar-open fill, worst-case stop first on dual-touch bars.

    Bar timestamps are OPEN times. The hypothesis.signal_time is a CLOSE time.
    The caller must independently validate session gaps and signal provenance.
    PnL is expressed in R multiples; no fabricated monetary profit.
    """
    if hypothesis.direction not in ('LONG', 'SHORT'):
        raise ValueError('Invalid direction')
    if not (math.isfinite(hypothesis.stop_distance) and hypothesis.stop_distance > 0):
        raise ValueError('Invalid stop distance')
    if not (math.isfinite(hypothesis.reward_to_risk) and hypothesis.reward_to_risk >= 2):
        raise ValueError('Minimum reward/risk is 2')
    if not (0 < risk_fraction <= .005):
        raise ValueError('Risk cap is 0.5%')
    if any(not math.isfinite(x) or x < 0 for x in (spread, slippage)):
        raise ValueError('Invalid execution costs')
    signal_time = _utc(hypothesis.signal_time)
    ordered = sorted(bars, key=lambda b: _utc(b.timestamp))
    times = [_utc(b.timestamp) for b in ordered]
    if len(times) != len(set(times)):
        raise ValueError('Duplicate candle timestamp')
    for b in ordered:
        if not all(math.isfinite(v) and v > 0 for v in (b.open, b.high, b.low, b.close)):
            raise ValueError('Invalid OHLC')
        if b.low > min(b.open, b.close) or b.high < max(b.open, b.close):
            raise ValueError('Invalid OHLC range')
    future = [b for b in ordered if _utc(b.timestamp) >= signal_time]
    base = {'decision': 'NO_TRADE', 'research_only': True, 'quality_certified': False,
            'research_signal_eligible': False, 'hypothetical': True}
    if not future:
        return {**base, 'outcome': 'unresolved', 'reason': 'No next execution candle', 'r_multiple': None}
    first = future[0]
    side = 1 if hypothesis.direction == 'LONG' else -1
    # Spread is paid as full round-trip cost: half at entry and half at exit.
    entry = first.open + side * (spread / 2 + slippage)
    stop = entry - side * hypothesis.stop_distance
    target = entry + side * hypothesis.stop_distance * hypothesis.reward_to_risk
    if entry <= 0 or stop <= 0 or target <= 0:
        return {**base, 'outcome': 'rejected', 'reason': 'Non-positive execution level', 'r_multiple': None}
    for b in future:
        # Stop takes precedence when both stop and target occur inside the same candle.
        stop_hit = b.low <= stop if side == 1 else b.high >= stop
        target_hit = b.high >= target if side == 1 else b.low <= target
        if stop_hit or target_hit:
            # A gap through stop is filled at worse of open and stop.
            if stop_hit:
                exit_price = min(b.open, stop) if side == 1 else max(b.open, stop)
                outcome = 'loss'
            else:
                exit_price = target  # no positive gap improvement assumption
                outcome = 'win'
            exit_price -= side * (spread / 2 + slippage)
            r = side * (exit_price - entry) / hypothesis.stop_distance
            return {**base, 'outcome': outcome, 'entry_time_utc': _utc(first.timestamp).isoformat(),
                    'exit_time_utc': _utc(b.timestamp).isoformat(), 'entry': entry,
                    'stop': stop, 'target': target, 'exit': exit_price,
                    'r_multiple': r, 'risk_fraction': risk_fraction,
                    'ambiguity_stop_first': bool(stop_hit and target_hit)}
    return {**base, 'outcome': 'unresolved', 'reason': 'Neither stop nor target reached',
            'entry_time_utc': _utc(first.timestamp).isoformat(), 'entry': entry,
            'stop': stop, 'target': target, 'r_multiple': None}
