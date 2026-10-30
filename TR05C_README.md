# TR-05C provisional holiday-aware backtest patch

Install from the repository root with `unzip -o ~/Downloads/TR05C-holiday-audit-patch.zip -d .`.

Run `uv run pytest -q tests/test_tr05c_calendar.py tests/trading/test_fx_session_validation.py tests/test_tr05b.py`.

Restart the FastAPI backend and run the EURUSD, GBPUSD, USDJPY historical backtests in `/trading/lab`.

## Safety and scope
- Preserves the original provisional session-audit behaviour by default. The exception calendar is explicitly applied ONLY to the OANDA historical research runner.
- Two exception windows (UTC, end exclusive): 2025-12-24 22:00 to 2025-12-25 22:00 and 2025-12-31 22:00 to 2026-01-01 22:00.
- **Important:** These intervals are based on the observed OANDA dataset gaps, not an independently verified broker holiday timetable. The calendar is named UNVERIFIED and `calendar_verified` remains false. Independently verify against authoritative OANDA schedules before certifying dataset continuity.
- Any candles inside excluded intervals, any other missing candles, invalid OHLC, duplicates or alignment errors continue to fail the audit.
- Does not modify historical CSVs, create synthetic bars, train models, or enable broker orders. It is not a full trusted dataset/versioning/training implementation.
- Existing strategy risk, NO_TRADE, and uncertified research posture remain unchanged.
