# TR-02A.2 — Yahoo Finance FX provider

Copy the `app/`, `scripts/` and `tests/` folders into the repository root without overwriting unrelated files.

Install dependencies: `uv add yfinance pandas`

Test: `uv run pytest tests/trading/test_yahoo_provider.py -v`

Try a one-day import (end exclusive):

`uv run python -m scripts.import_yahoo EURUSD H1 2026-10-20 2026-10-21`

Other examples:

`uv run python -m scripts.import_yahoo GBPUSD M15 2026-10-20 2026-10-21`

`uv run python -m scripts.import_yahoo USDJPY D1 2026-10-01 2026-10-21`

The importer does not overwrite existing output. Data is written under `data/forex/historical_real/`, separate from synthetic fixtures. The existing API and dashboard are intentionally unchanged. Yahoo's availability and historical retention vary; a request may return no data or be rate-limited. No completeness or executable-price guarantee is made. Verify applicable Yahoo terms before commercial use.
