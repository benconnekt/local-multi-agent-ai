# TR-03A — Research-only multi-timeframe strategy

Copy `app/trading/strategies/multi_timeframe.py` and `tests/trading/test_multi_timeframe.py` into the repository without overwriting unrelated files.

Run `uv run pytest tests/trading/test_multi_timeframe.py -v` and `uv run pytest -q`.

Usage:

```python
from app.trading.strategies.multi_timeframe import evaluate
signal = evaluate(h4_candles, h1_candles, m15_candles,
                  as_of="2026-10-30T12:00:00Z", quality_certified=False)
print(signal.to_dict())
```

**IMPORTANT**: `quality_certified=True` must be supplied only by a trusted upstream quality gate after checking the specific datasets and alignment. Never set it merely to force a signal. The current TR-02C `coverage_pass_weekend_model_only` is not full certification. The strategy is deliberately fail-closed until that gate is implemented.

This is a research hypothesis, not a profitable or live-ready strategy. It has no API route, no broker connection, no execution, no position-sizing calculation, and no backtesting integration. ATR-based levels use indicative candle-close entries, not fills. H1 EMA pullback proximity is checked against the current H1 EMA as a simplified heuristic. Future iterations must enforce consistent as-of slicing across timeframes, session calendars, historical data quality and realistic trading costs before backtesting.
