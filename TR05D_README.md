# TR-05D: Historical hypothesis generator performance correction

This patch changes only `app/trading/research/hypothesis_generator.py` and adds a regression test. It precomputes closed H1/H4 candle indexes and EMA series, then uses binary searches to select data available at each M15 signal close. No broker integration or trading authorization is added.

Install from repository root:

    unzip -o ~/Downloads/TR05D-backtest-performance.zip -d .
    uv run pytest -q tests/trading/test_tr03a14_hypothesis_generator.py tests/trading/test_tr05d_hypothesis_performance.py

Restart FastAPI, then run the backtest. Do not run concurrent requests until latency is verified.

Verification: 9 targeted tests passed in the provided code snapshot. Comparison against the original implementation on synthetic 1100 H1 / 4400 M15 bars yielded identical output and rejected counts (reference 5.169 seconds, optimized 0.015 seconds in this container). Actual full-year data and frontend performance were not tested here because historical CSVs were excluded from the uploaded project archive.

Safety: research-only, NO_TRADE, no broker orders, no strategy promotion. Existing holiday calendar patch must remain installed.
