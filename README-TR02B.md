# TR-02B — dataset discovery (additive patch)

This patch adds a **separate** read-only dataset API and updates the standalone `/trading` page. It does not change Engineering or the existing `/trading/candles` synthetic endpoint.

1. Extract to the **repository root**. Back up `apps/web/app/trading/page.tsx` before replacing it; the other files are new.
2. In `app/api/main.py`, import `from app.api.routes import trading_datasets` and register `app.include_router(trading_datasets.router, prefix='/api/v1')` **once**, alongside existing routers. Do not create a second FastAPI app.
3. Run `uv run pytest tests/trading/test_dataset_catalogue.py -v` and `uv run pytest -q`.
4. Run `cd apps/web && npx tsc --noEmit && npm run lint && npm run build`.
5. Restart both servers. Visit `/api/v1/trading/datasets` and `/trading`.

Only Yahoo CSV+JSON pairs with matching metadata, checksum, valid OHLC, count and monotonic timestamps are discoverable. **This is not a completeness certification**: no full-session gap detection yet. The code re-reads files on requests and is intended for small local datasets; add indexing/caching and stronger metadata schema before scaling.

If the local page has been customised since TR-01C, merge the frontend change manually rather than overwriting it.
