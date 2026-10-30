# TR-05 integrated foundation (research only)

This patch is **not** the full TR-05 programme. It introduces a safe strategy catalogue, close-price indicator diagnostics, cost-sensitive retrospective ledger diagnostics, research-only API routes, and a functioning Strategy Lab frontend. It does **not** implement independently validated walk-forward experiments, reliable sentiment, adaptive agent training, or forward paper observation. No profitable strategy is claimed.

## Install

Back up/commit first. From the project root unzip the patch, then:

```sh
uv run pytest -q tests/test_tr05_lab.py
uv run uvicorn app.api.main:app --reload --env-file .env
# another terminal
cd apps/web && npm run typecheck && npm run build && npm run dev
```

Open `/trading/lab`. API: `GET /api/v1/trading/agents/lab/overview`, `POST /indicators` with `{ "closes": [ ... ] }`, `POST /diagnostics` with `{ "ledger": [...], "cost_r": 0.1 }`. No endpoint sends orders. The diagnostics UI accepts only user-supplied historical trade data; it does not simulate or manufacture results. The ledger endpoint requires strictly increasing ISO UTC `Z` timestamps and outcome-consistent realised R.

## Next validation gates

1. Reconcile original historical datasets, candles and provenance; freeze strategy version before new observations.
2. Add real OHLC ATR, swings, market regime and actual spread/commission evidence.
3. Build strategy experiment runner with immutable versioned manifests, chronological folds and genuine held-out datasets.
4. Connect verified hypothetical ledger exports without manual copy/paste; report per-pair cost and slippage sensitivities.
5. Persist forward paper observations and measure drift over newly arriving data; never send broker orders.
6. Independent data, backtest and safety certification plus explicit authorization before considering execution.

Do not place `.env` or OANDA tokens in ZIP files or commit history.
