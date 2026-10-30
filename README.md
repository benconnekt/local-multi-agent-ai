# TR-05C.2 — Historical reconciliation diagnostics

This patch does **not** pretend that GBPUSD's 2025-12-21 22:15 UTC M15 candle exists. The research gate remains closed until that gap is resolved. It preserves the previous TR-05C provisional closure calendar and does not certify broker holidays.

Install from repository root: `unzip -o ~/Downloads/TR05C2-reconciliation.zip -d .`.

Run `uv run python scripts/tr05c2_reconcile.py` to see calendar-adjusted audit results for all three pairs. Expect EURUSD and USDJPY H1/M15 to pass, GBPUSD H1 to pass, GBPUSD M15 to show one missing interval. Results depend on your imported files.

For a **read-only** broker probe, ensure `OANDA_API_TOKEN` is in the environment (do not share it), `OANDA_ENVIRONMENT=practice`, then run `uv run python scripts/tr05c2_oanda_probe.py`. It requests only GBP_USD M15 candles 2025-12-21 22:00–23:00 UTC and prints what the broker returns. No automatic import is performed: reconcile any returned candle through the existing validated importer, and re-run the audit. If no candle is returned, do not invent one or silently waive the gap.

The historical backtest now provides detailed audit failures rather than a generic error. This patch is based on the previously delivered TR-05C holiday-calendar version of the runner; it does not include or alter the TR-05D hypothesis-generator performance fix.
