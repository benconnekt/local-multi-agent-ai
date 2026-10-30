# TR-03A.1: Read-only strategy readiness integration

This is a deliberately fail-closed first integration, NOT a working BUY/SELL signal generator. The existing quality status `coverage_pass_weekend_model_only` cannot certify strategy readiness. Cross-timeframe alignment, dataset merging, H4 generation, market calendar, and sufficient EMA200 warm-up remain prerequisites.

## Install
From project root, unzip with `unzip -n ~/Downloads/tr03a1-strategy-integration.zip -d .` (new files only).

In `app/api/main.py`, add `from app.api.routes import trading_strategy` and `app.include_router(trading_strategy.router, prefix="/api/v1")` once, without removing existing routers.

In `apps/web/app/trading/page.tsx`, add `import StrategyResearchPanel from '../../components/trading/StrategyResearchPanel';` and place `<StrategyResearchPanel instrument={mode === 'historical' ? (historical?.instrument ?? datasets.find(d => d.id === selectedId)?.instrument ?? 'EURUSD') : instrument} />` immediately after the chart section. This shows real-data readiness even in synthetic chart mode; the panel NEVER evaluates synthetic candles.

Run `uv run pytest tests/trading/test_strategy_route.py -v && uv run pytest -q`, then `cd apps/web && npx tsc --noEmit && npm run lint && npm run build`.

GET `/api/v1/trading/strategy/analyse?instrument=EURUSD` should return NO_TRADE with missing timeframe and/or uncertified-data reasons.

**No execution and no signal authorisation.** This is a readiness UI, not TR-03A.1 complete signal evaluation. Do not change status to BUY/SELL by toggling a flag; a fully tested quality and aligned-data integration is required.
