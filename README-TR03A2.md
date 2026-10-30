# TR-03A.2 — Conservative historical strategy loader

This is an **intermediate fail-closed backend integration**, not an enabled BUY/SELL signal engine. It intentionally does not call `evaluate(..., quality_certified=True)` because the current project lacks an independently verified FX session/holiday calendar and sufficient continuous multi-timeframe history. It rejects all research signals while reporting why.

## Install (review first)

From `/Users/ben/Projects/multi_agent_ai`:

```sh
unzip -l ~/Downloads/tr03a2-backend.zip
cp app/api/routes/trading_strategy.py app/api/routes/trading_strategy.py.before-tr03a2
unzip -n ~/Downloads/tr03a2-backend.zip -d .
# Existing route must be replaced intentionally after review:
unzip -p ~/Downloads/tr03a2-backend.zip app/api/routes/trading_strategy.py > app/api/routes/trading_strategy.py
uv run pytest tests/trading/test_strategy_data_loader.py -v
uv run pytest -q
```

No new router registration required: existing `trading_strategy.router` remains registered.

## Current restrictions

- `discover()` still validates Yahoo metadata, CSV hash and OHLC.
- Merging rejects conflicting overlapping candles, excludes unclosed candles, and preserves source IDs.
- Strict contiguous gap checks reject weekends; a proper FX trading calendar is needed to certify longer datasets.
- H4 aggregation only includes complete UTC 4-hour groups; absent volume remains null.
- Strategy signals are **always NO_TRADE** in this milestone. No live orders.
- Current one-day data cannot meet EMA 200 on H4.
- Next milestone: independently certified session calendar, quality windows, cutoff alignment, EMA pullback correction, and actual `evaluate()` call with tested authorization conditions.
