# TR-03A.5 — Phase 1: FX session diagnostics

This is **not** market-session certification. It adds a non-invasive, deterministic
calendar-assumption audit without changing the working `assemble()` function or
`/trading/strategy/analyse` response. `NO_TRADE` remains mandatory.

## Install

From repository root:

```bash
unzip -n ~/Downloads/tr03a5-session-audit.zip -d .
uv run pytest tests/trading/test_fx_session_audit.py -v
uv run pytest -q
```

## Use with real candles

```python
from app.trading.quality.fx_session_audit import audit_candles
result = audit_candles(dataset['candles'], 'H1')
print(result.to_dict())
```

## Limitations and next steps

- Sunday 22:00 UTC to Friday 22:00 UTC is **only a simplified assumption**.
  US/UK DST transitions, holidays, broker conventions and Yahoo coverage can differ.
- An audit checks gaps only *between* first and last timestamps; it cannot establish
  the requested date-range coverage, candle integrity, freshness, or provenance.
- No independent calendar has been integrated. `certified` always stays `False`.
- Next: obtain documented provider-specific sessions and holiday exceptions; validate
  against independent reference; certify requested coverage windows; enforce same-symbol
  H1/M15 overlap, closed-bar alignment, minimum H4 warm-up, and risk gates.
- Do not remove the final `DatasetNotReady` raise in `assemble()` until those gates
  are implemented and tested. Do not infer H4 readiness from H1 presence alone.
