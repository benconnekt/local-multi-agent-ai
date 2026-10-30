"""Deterministic, read-only H4/H1/M15 hypothesis discovery.

All Bar timestamps denote candle OPEN; only closed candles can inform a signal.
Inputs must be provider-scoped, audited and reconciled before use. Never routes orders.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from bisect import bisect_right
from math import isfinite
from typing import Iterable

from app.trading.research.backtest import Bar, Hypothesis

H1 = timedelta(hours=1)
M15 = timedelta(minutes=15)
H4 = timedelta(hours=4)


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise ValueError('Timezone-aware candle timestamps required')
    return value.astimezone(timezone.utc)


def _validated(rows: Iterable[Bar], step: timedelta) -> list[Bar]:
    ordered = sorted(rows, key=lambda x: _utc(x.timestamp))
    times = [_utc(x.timestamp) for x in ordered]
    if len(times) != len(set(times)):
        raise ValueError('Duplicate candle timestamps')
    for bar, ts in zip(ordered, times):
        if (ts - datetime(1970, 1, 1, tzinfo=timezone.utc)) % step:
            raise ValueError('Misaligned candle timestamp')
        if not all(isfinite(v) and v > 0 for v in (bar.open, bar.high, bar.low, bar.close)):
            raise ValueError('Invalid OHLC values')
        if bar.low > min(bar.open, bar.close) or bar.high < max(bar.open, bar.close):
            raise ValueError('Invalid OHLC range')
    return ordered


def _ema(values: list[float], period: int) -> float | None:
    if len(values) < period:
        return None
    result = sum(values[:period]) / period
    weight = 2 / (period + 1)
    for value in values[period:]:
        result = result + weight * (value - result)
    return result


def _atr(rows: list[Bar], period: int = 14) -> float | None:
    if len(rows) < period + 1:
        return None
    ranges = []
    for prev, curr in zip(rows[-period-1:-1], rows[-period:]):
        ranges.append(max(curr.high - curr.low, abs(curr.high - prev.close), abs(curr.low - prev.close)))
    return sum(ranges) / period


def _h4_from_h1(rows: list[Bar], cutoff: datetime) -> list[Bar]:
    buckets: dict[datetime, dict[datetime, Bar]] = {}
    for bar in rows:
        ts = _utc(bar.timestamp)
        if ts + H1 > cutoff:
            continue
        bucket = ts.replace(hour=ts.hour // 4 * 4, minute=0, second=0, microsecond=0)
        buckets.setdefault(bucket, {})[ts] = bar
    output = []
    for start, group in sorted(buckets.items()):
        slots = [start + i * H1 for i in range(4)]
        if start + H4 > cutoff or set(group) != set(slots):
            continue
        bars = [group[t] for t in slots]
        output.append(Bar(start, bars[0].open, max(x.high for x in bars),
                          min(x.low for x in bars), bars[-1].close))
    return output


def _ema_prefix(values: list[float], period: int) -> list[float | None]:
    """EMA for every closed-bar prefix, with identical seeding to _ema."""
    result: list[float | None] = [None] * len(values)
    if len(values) < period:
        return result
    current = sum(values[:period]) / period
    result[period - 1] = current
    weight = 2 / (period + 1)
    for i in range(period, len(values)):
        current += weight * (values[i] - current)
        result[i] = current
    return result


def _complete_h4(rows: list[Bar]) -> list[Bar]:
    """Build complete UTC-aligned H4 candles once, never filling gaps."""
    buckets: dict[datetime, dict[datetime, Bar]] = {}
    for bar in rows:
        ts = _utc(bar.timestamp)
        start = ts.replace(hour=ts.hour // 4 * 4, minute=0, second=0, microsecond=0)
        buckets.setdefault(start, {})[ts] = bar
    result = []
    for start, group in sorted(buckets.items()):
        slots = [start + i * H1 for i in range(4)]
        if set(group) != set(slots):
            continue
        bars = [group[t] for t in slots]
        result.append(Bar(start, bars[0].open, max(x.high for x in bars),
                          min(x.low for x in bars), bars[-1].close))
    return result


def discover_hypotheses(h1_rows: Iterable[Bar], m15_rows: Iterable[Bar], *,
                        as_of: datetime, minimum_h4: int = 250,
                        atr_multiplier: float = 1.5,
                        reward_to_risk: float = 2.0) -> dict:
    """Return timestamped *hypotheses*, never trade authorisations.

    Conservative initial rules: H4 EMA50/200 trend; previous closed H1
    candle touches H1 EMA20 and closes on trend side; last closed M15 candle
    breaks the preceding three closed M15 highs/lows. Each decision uses only
    bars closed by its own signal timestamp, not the final as_of timestamp.
    """
    if minimum_h4 < 200 or not isfinite(atr_multiplier) or atr_multiplier <= 0:
        raise ValueError('Invalid warm-up or ATR multiplier')
    if not isfinite(reward_to_risk) or reward_to_risk < 2:
        raise ValueError('Minimum reward/risk is 2')
    cutoff = _utc(as_of)
    h1 = _validated(h1_rows, H1)
    m15 = _validated(m15_rows, M15)
    # Precompute indicators and candle close timestamps once. Every lookup below
    # uses bisect_right(close_time), preventing future candles from leaking in.
    h1_closes = [_utc(x.timestamp) + H1 for x in h1]
    h4 = _complete_h4(h1)
    h4_closes = [_utc(x.timestamp) + H4 for x in h4]
    h1_ema20 = _ema_prefix([x.close for x in h1], 20)
    h4_ema50 = _ema_prefix([x.close for x in h4], 50)
    h4_ema200 = _ema_prefix([x.close for x in h4], 200)
    candidates = []
    rejected = {'insufficient_h4': 0, 'no_trend': 0, 'insufficient_h1': 0,
                'no_pullback': 0, 'no_breakout': 0, 'invalid_atr': 0}
    for i in range(3, len(m15)):
        signal = m15[i]
        close_time = _utc(signal.timestamp) + M15
        if close_time > cutoff:
            break
        h1_count = bisect_right(h1_closes, close_time)
        h4_count = bisect_right(h4_closes, close_time)
        if h4_count < minimum_h4:
            rejected['insufficient_h4'] += 1
            continue
        ema50 = h4_ema50[h4_count - 1]
        ema200 = h4_ema200[h4_count - 1]
        if ema50 is None or ema200 is None or ema50 == ema200:
            rejected['no_trend'] += 1
            continue
        direction = 'LONG' if ema50 > ema200 else 'SHORT'
        if h1_count < 21:
            rejected['insufficient_h1'] += 1
            continue
        previous_h1 = h1[h1_count - 1]
        ema20 = h1_ema20[h1_count - 1]
        pulled_back = (previous_h1.low <= ema20 < previous_h1.close if direction == 'LONG'
                       else previous_h1.high >= ema20 > previous_h1.close)
        if not pulled_back:
            rejected['no_pullback'] += 1
            continue
        prior = m15[i-3:i]
        breakout = (signal.close > max(x.high for x in prior) if direction == 'LONG'
                    else signal.close < min(x.low for x in prior))
        if not breakout:
            rejected['no_breakout'] += 1
            continue
        atr = _atr(h1[max(0, h1_count - 15):h1_count])
        if atr is None or not isfinite(atr) or atr <= 0:
            rejected['invalid_atr'] += 1
            continue
        hypothesis = Hypothesis(direction, close_time, atr * atr_multiplier, reward_to_risk)
        candidates.append({'hypothesis': hypothesis, 'evidence': {
            'signal_close_utc': close_time.isoformat(), 'h4_last_close_utc':
                h4_closes[h4_count - 1].isoformat(),
            'h1_last_close_utc': (_utc(previous_h1.timestamp) + H1).isoformat(),
            'ema50_h4': ema50, 'ema200_h4': ema200, 'ema20_h1': ema20,
            'atr14_h1': atr, 'breakout_lookback_m15': 3}})
    return {'decision': 'NO_TRADE', 'research_only': True,
            'quality_certified': False, 'research_signal_eligible': False,
            'hypothetical': True, 'as_of_utc': cutoff.isoformat(),
            'hypotheses': candidates, 'rejected_counts': rejected,
            'evaluated_m15_candles': max(0, sum(_utc(x.timestamp) + M15 <= cutoff for x in m15) - 3),
            'warning': 'Requires independent provider/session certification; not for order routing'}
