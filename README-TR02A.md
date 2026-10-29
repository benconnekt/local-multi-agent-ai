# TR-02A: Dukascopy tick-to-candle importer (initial research implementation)

This importer is **not yet wired to the dashboard or the existing `/trading/candles` API**. The existing synthetic fixtures remain unchanged. It uses the public Dukascopy hourly BI5 tick archive; verify availability and terms of use before depending on it. Network retrieval is not tested in this environment.

Run from repository root:

```bash
uv run pytest tests/trading/test_dukascopy.py -q
uv run python scripts/import_dukascopy.py EURUSD 2026-10-20 2026-10-21
```

The end date is exclusive; choose a known fully active trading day (not weekends or holidays). A maximum of 7 days is allowed per invocation. All 24 hourly files must contain ticks; missing or empty hours fail closed rather than being silently filled. This strict first version will reject days containing market closures and some legitimate low-liquidity gaps. No automatic retries or backfilling.

Output: `data/forex/historical_real/` with distinct dated CSV and adjacent JSON provenance. Files are never intentionally overwritten. Do not commit real market data without checking provider licensing. No live prices, signals, broker connectivity, trading, or claims of profitability. Bid prices and reported bid tick volume are **not** executable quotes or exchange-traded volume. Realistic backtests will also require spreads, commissions, slippage, market sessions, and coverage checks.

**Known limitation:** publication of the CSV and metadata is not transactional; if metadata writing fails, a CSV may remain without provenance. The next hardening step is staging a complete pair, validating the result, and atomically publishing a manifest, plus checksums and import retries. Do not use partially imported output for research.
