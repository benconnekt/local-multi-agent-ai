"""Deterministic, research-only multi-timeframe trend/pullback strategy.

All inputs must be closed, UTC-aligned, validated historical candles. This
module never fetches market data or places orders. Decisions are hypotheses.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone, timedelta
from math import isfinite
from typing import Any, Literal, Mapping, Sequence

Decision = Literal['BUY', 'SELL', 'NO_TRADE']

@dataclass(frozen=True)
class StrategyConfig:
    fast_ema: int = 50
    slow_ema: int = 200
    atr_period: int = 14
    atr_stop_multiplier: float = 1.5
    reward_to_risk: float = 2.0
    max_risk_fraction: float = 0.005
    pullback_atr_tolerance: float = 0.5

    def __post_init__(self) -> None:
        if not (1 < self.fast_ema < self.slow_ema):
            raise ValueError('EMA periods must satisfy 1 < fast < slow')
        if self.atr_period < 2 or self.atr_stop_multiplier <= 0:
            raise ValueError('Invalid ATR configuration')
        if self.reward_to_risk < 2 or not (0 < self.max_risk_fraction <= 0.005):
            raise ValueError('Risk limits exceeded')
        if self.pullback_atr_tolerance <= 0:
            raise ValueError('Invalid pullback tolerance')

@dataclass(frozen=True)
class Signal:
    decision: Decision
    reason: str
    as_of_utc: str | None = None
    entry: float | None = None
    stop_loss: float | None = None
    take_profit: float | None = None
    risk_fraction: float = 0.0
    reward_to_risk: float | None = None
    indicators: dict[str, float] | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

@dataclass(frozen=True)
class _Bar:
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float


def _parse_timestamp(value: Any) -> datetime:
    if isinstance(value, datetime):
        dt = value
    elif isinstance(value, str):
        dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
    else:
        raise ValueError('Timestamp must be an ISO-8601 string or datetime')
    if dt.tzinfo is None:
        raise ValueError('Naive timestamps are forbidden')
    return dt.astimezone(timezone.utc)


def _read_bars(rows: Sequence[Mapping[str, Any]], minutes: int) -> list[_Bar]:
    result: list[_Bar] = []
    previous: datetime | None = None
    for row in rows:
        t = _parse_timestamp(row['timestamp'])
        if t.minute % minutes != 0 if minutes < 60 else (t.hour * 60 + t.minute) % minutes != 0:
            raise ValueError('Misaligned candle timestamp')
        if t.second or t.microsecond:
            raise ValueError('Candle timestamp must align to a minute')
        o, h, l, c = (float(row[k]) for k in ('open', 'high', 'low', 'close'))
        if not all(isfinite(x) and x > 0 for x in (o, h, l, c)):
            raise ValueError('Non-finite or non-positive OHLC')
        if l > min(o, c) or h < max(o, c) or h < l:
            raise ValueError('Inconsistent OHLC')
        if previous is not None and t <= previous:
            raise ValueError('Candles must be strictly increasing without duplicates')
        result.append(_Bar(t, o, h, l, c))
        previous = t
    return result


def _ema(values: Sequence[float], period: int) -> float:
    if len(values) < period:
        raise ValueError('Insufficient EMA history')
    ema = sum(values[:period]) / period
    alpha = 2 / (period + 1)
    for v in values[period:]:
        ema += alpha * (v - ema)
    return ema


def _atr(bars: Sequence[_Bar], period: int) -> float:
    if len(bars) < period + 1:
        raise ValueError('Insufficient ATR history')
    tr = [max(b.high - b.low, abs(b.high - bars[i - 1].close), abs(b.low - bars[i - 1].close))
          for i, b in enumerate(bars) if i > 0]
    atr = sum(tr[:period]) / period
    for v in tr[period:]:
        atr = (atr * (period - 1) + v) / period
    return atr


def evaluate(
    h4: Sequence[Mapping[str, Any]],
    h1: Sequence[Mapping[str, Any]],
    m15: Sequence[Mapping[str, Any]],
    *,
    as_of: str | datetime,
    quality_certified: bool,
    config: StrategyConfig | None = None,
) -> Signal:
    """Evaluate closed bars only; `as_of` is the decision timestamp (UTC).

    Inputs must be independently quality-checked for market-session gaps,
    provenance and coverage. Missing certification always means NO_TRADE.
    """
    cfg = config or StrategyConfig()
    try:
        now = _parse_timestamp(as_of)
    except (ValueError, TypeError):
        return Signal('NO_TRADE', 'Invalid as_of timestamp')
    stamp = now.isoformat()
    if not quality_certified:
        return Signal('NO_TRADE', 'Data quality is not certified', stamp)
    try:
        a, b, c = (_read_bars(rows, minutes) for rows, minutes in ((h4, 240), (h1, 60), (m15, 15)))
    except (KeyError, TypeError, ValueError, OverflowError) as exc:
        return Signal('NO_TRADE', f'Invalid candle data: {exc}', stamp)
    if len(a) < cfg.slow_ema or len(b) < max(cfg.fast_ema, cfg.atr_period + 1) or len(c) < cfg.atr_period + 2:
        return Signal('NO_TRADE', 'Insufficient candle history', stamp)
    # Candles are indexed by opening timestamp; exclude unfinished bars.
    for bars, duration in ((a, 240), (b, 60), (c, 15)):
        if any(bar.timestamp + timedelta(minutes=duration) > now for bar in bars):
            return Signal('NO_TRADE', 'Unclosed/future candle supplied', stamp)
    # Enforce freshness and avoid decisions based on stale weekend or missing bars.
    if (now - c[-1].timestamp > timedelta(minutes=30)
        or now - b[-1].timestamp > timedelta(hours=2)
        or now - a[-1].timestamp > timedelta(hours=8)):
        return Signal('NO_TRADE', 'Stale timeframe data', stamp)
    fast = _ema([x.close for x in a], cfg.fast_ema)
    slow = _ema([x.close for x in a], cfg.slow_ema)
    h1_fast = _ema([x.close for x in b], cfg.fast_ema)
    atr = _atr(b, cfg.atr_period)
    if atr <= 0:
        return Signal('NO_TRADE', 'Zero ATR', stamp)
    direction = 1 if a[-1].close > fast > slow else -1 if a[-1].close < fast < slow else 0
    if not direction:
        return Signal('NO_TRADE', 'No aligned H4 trend', stamp)
    # Previous H1 candle must touch the fast EMA neighbourhood; latest H1
    # candle must resume in the trend direction. Deliberately conservative.
    previous = b[-2]
    latest = b[-1]
    touched = (previous.low <= h1_fast + cfg.pullback_atr_tolerance * atr
               and previous.high >= h1_fast - cfg.pullback_atr_tolerance * atr)
    resumed = (latest.close > latest.open and latest.close > h1_fast) if direction == 1 else (latest.close < latest.open and latest.close < h1_fast)
    if not (touched and resumed):
        return Signal('NO_TRADE', 'No confirmed H1 pullback and resumption', stamp)
    # Require last two M15 candles to show directional momentum and a break
    # of the preceding candle's high/low, using closed candles only.
    prior, trigger = c[-2], c[-1]
    confirmed = (trigger.close > trigger.open and trigger.close > prior.high) if direction == 1 else (trigger.close < trigger.open and trigger.close < prior.low)
    if not confirmed:
        return Signal('NO_TRADE', 'No M15 entry confirmation', stamp)
    entry = trigger.close  # Indicative close, not an executable fill.
    distance = cfg.atr_stop_multiplier * atr
    stop = entry - direction * distance
    target = entry + direction * cfg.reward_to_risk * distance
    if stop <= 0 or target <= 0:
        return Signal('NO_TRADE', 'Invalid stop or target', stamp)
    return Signal(
        'BUY' if direction == 1 else 'SELL',
        'H4 trend, H1 pullback/resumption and M15 breakout confirmed; research-only',
        stamp, entry, stop, target, cfg.max_risk_fraction, cfg.reward_to_risk,
        {'h4_ema_fast': fast, 'h4_ema_slow': slow, 'h1_ema_fast': h1_fast, 'h1_atr': atr},
    )
