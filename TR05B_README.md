# TR-05B — Automated historical backtest integration

Incremental patch **on top of FE-01 and TR-05 Research Foundation**. Does not overwrite `.env` or datasets.

Adds read-only endpoints:
- GET `/api/v1/trading/agents/lab/historical/datasets`
- POST `/api/v1/trading/agents/lab/historical/backtest` with `{"instrument":"EURUSD","spread":0.0001,"slippage":0.00002}`

The historical runner is reused unchanged; audit_report reconciles results. This does not implement trend-pullback, breakout-retest, liquidity-sweep, walk-forward or forward paper research.

## Install

```sh
cd /Users/ben/Projects/multi_agent_ai
unzip -o ~/Downloads/TR05B-automated-history-lab.zip -d .
uv run pytest -q tests/test_tr05_lab.py tests/test_tr05b.py
uv run uvicorn app.api.main:app --reload --env-file .env
```

In another terminal: `cd apps/web && npm run typecheck && npm run build && npm run dev`.

Open `/trading/lab` and select a pair. Import H1 and M15 data beforehand. A missing or failed provisional session audit returns HTTP 422; it is not silently bypassed. Spread and slippage are raw instrument price units, not pips. Defaults are zero **only for diagnostics**, not credible net-performance claims.

**Safety:** NO_TRADE, no broker mutations, no automatic promotion, no independent certification. Reconciliation audit is not certification. Do not upload credentials.
