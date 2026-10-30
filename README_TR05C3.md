# TR-05C.3 — Broker-observed absence reconciliation

Apply at project root: `unzip -o TR05C3-broker-absence.zip -d .`

Run: `uv run pytest -q tests/test_tr05c3_absences.py`

Audit: `PYTHONPATH=. uv run python scripts/tr05c2_reconcile.py`

Backtest via existing API. This patch does not query OANDA, write imported CSVs, or execute orders.

The sole exception is OANDA v20 GBPUSD M15 2025-12-21T22:15Z, observed absent from the practice broker's read-only candle response. Not a verified closure. The runner already rejects nonconsecutive M15 breakout windows via `_continuous`. No fabricated OHLC. Holiday calendar still provisional; no independent certification.
