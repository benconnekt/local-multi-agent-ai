# TR-03A.6 — Conservative FX session readiness

## Scope
Adds a **provisional** Sunday 22:00 UTC–Friday 22:00 UTC session audit, H4 completeness summary, and API-ready diagnostic payload. **Does not certify Yahoo data or permit signals**. Provider-specific DST, holidays, early closes, outage reconciliation, candle-close conventions and independent validation remain outstanding. The fixed UTC weekend schedule will misclassify some DST periods; do not use it as an authoritative FX calendar.

## Install
From the repo root: `unzip -n ~/Downloads/TR-03A6-fx-session-readiness.zip -d .`

## Wire the API (manual, additive)
In `app/api/routes/trading_strategy.py`, add:

```python
from app.trading.quality.readiness_report import build_session_readiness
```

After `entries` is created, add:

```python
session_readiness = build_session_readiness(entries)
```

In the returned dictionary add:

```python
'session_readiness': session_readiness,
```

Do **not** change the existing `assemble(...)` try/except, `NO_TRADE`, `quality_certified=False`, or `unavailable_score(reason)`.

### Optional dashboard (inside `{report && ...}`)
Add a `session_readiness` field to `Report`:

```ts
session_readiness?: {
  H1?: { candle_count: number; missing_expected_candles: number; provisional_schedule_pass: boolean };
  M15?: { candle_count: number; missing_expected_candles: number; provisional_schedule_pass: boolean };
  H4?: { complete_candles: number; incomplete_groups: number; history_sufficient: boolean };
  certification_status?: string;
};
```

Then render:

```tsx
{report.session_readiness && (
  <div className="rounded-lg border border-slate-700 p-3 text-sm text-slate-300">
    <h3 className="font-semibold">FX session audit (provisional)</h3>
    {(["H1", "M15"] as const).map(tf => {
      const data = report.session_readiness?.[tf];
      return <p key={tf}>{tf}: {data?.candle_count ?? 0} candles; {data?.missing_expected_candles ?? 0} expected slots missing; provisional audit {data?.provisional_schedule_pass ? "pass" : "not passed"}</p>;
    })}
    <p>H4: {report.session_readiness.H4?.complete_candles ?? 0} complete derived candles; {report.session_readiness.H4?.incomplete_groups ?? 0} incomplete groups</p>
    <p className="text-amber-300">Independent certification pending. Research signals disabled.</p>
  </div>
)}
```

## Tests
`uv run pytest tests/trading/test_fx_session_validation.py -v`
`uv run pytest -q`

## Limitations / next gate
1. Confirm the Yahoo candle timestamp convention (open vs close), provider trading sessions and timezone/DST behavior.
2. Reconcile duplicate overlapping data and distinguish missing intervals from holidays/early closes/outages using an authoritative, versioned calendar.
3. Collect sufficient same-instrument H1/M15 data; derive and verify H4 bars and EMA warm-up.
4. Independently validate source provenance, OHLC, market sessions and completeness; then implement a separate certification authority. Do not set `quality_certified=True` merely because this audit passes.
5. The audit iterates expected time slots between observed endpoints; use bounded date ranges for performance.
