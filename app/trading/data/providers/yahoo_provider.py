"""Yahoo Finance historical FX adapter. Research only; not an execution feed."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from app.trading.data.models import Candle, Instrument, Timeframe


class YahooDataError(ValueError):
    """Yahoo returned unavailable, incomplete or invalid market data."""


SYMBOLS = {
    Instrument.EURUSD: "EURUSD=X",
    Instrument.GBPUSD: "GBPUSD=X",
    Instrument.USDJPY: "JPY=X",
}
INTERVALS = {Timeframe.M15: "15m", Timeframe.H1: "60m", Timeframe.D1: "1d"}


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise YahooDataError("Dates must include a timezone")
    return value.astimezone(timezone.utc)


def parse_yahoo_frame(frame: Any) -> list[Candle]:
    """Convert a single-symbol yfinance DataFrame to validated UTC candles."""
    if frame is None or frame.empty:
        raise YahooDataError("Yahoo returned no candles for this date range")
    if getattr(frame.columns, "nlevels", 1) != 1:
        raise YahooDataError("Expected single-level OHLC columns; use multi_level_index=False")
    required = ("Open", "High", "Low", "Close")
    if any(col not in frame.columns for col in required):
        raise YahooDataError("Yahoo response is missing required OHLC columns")
    result: list[Candle] = []
    for timestamp, row in frame.iterrows():
        dt = timestamp.to_pydatetime() if hasattr(timestamp, "to_pydatetime") else timestamp
        if not isinstance(dt, datetime) or dt.tzinfo is None or dt.utcoffset() is None:
            raise YahooDataError("Yahoo returned an unzoned timestamp")
        try:
            result.append(Candle(
                timestamp=dt,
                open=float(row["Open"]), high=float(row["High"]),
                low=float(row["Low"]), close=float(row["Close"]),
                volume=None,  # Yahoo FX volume is not reliable exchange volume.
            ))
        except (ValueError, TypeError) as exc:
            raise YahooDataError(f"Invalid Yahoo candle at {dt.isoformat()}: {exc}") from exc
    if any(b.timestamp <= a.timestamp for a, b in zip(result, result[1:])):
        raise YahooDataError("Yahoo candles contain duplicates or out-of-order timestamps")
    return result


class YahooFinanceProvider:
    """Fetch historical FX candles; caller owns persistence and provenance."""

    def load(self, instrument: Instrument, timeframe: Timeframe,
             start: datetime, end: datetime) -> list[Candle]:
        start, end = _as_utc(start), _as_utc(end)
        if start >= end:
            raise YahooDataError("Start must precede end")
        if timeframe not in INTERVALS:
            raise YahooDataError(f"Unsupported Yahoo interval: {timeframe.value}")
        if timeframe == Timeframe.M15 and end - start > timedelta(days=60):
            raise YahooDataError("M15 requests must cover at most 60 days; Yahoo may restrict older intraday history")
        try:
            import yfinance as yf
        except ImportError as exc:
            raise YahooDataError("Install yfinance with: uv add yfinance") from exc
        try:
            frame = yf.download(
                SYMBOLS[instrument], start=start, end=end,
                interval=INTERVALS[timeframe], auto_adjust=False,
                progress=False, threads=False, multi_level_index=False,
            )
        except Exception as exc:
            raise YahooDataError(f"Yahoo request failed: {type(exc).__name__}: {exc}") from exc
        candles = parse_yahoo_frame(frame)
        # A provider may return a candle at the boundary: enforce requested range.
        if any(not start <= candle.timestamp < end for candle in candles):
            raise YahooDataError("Yahoo returned candles outside requested range")
        return candles
