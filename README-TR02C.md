# TR-02C quality engine (incremental)

Adds standalone `app/trading/quality/validation.py` and six tests. Does not overwrite existing routes, providers, UI or datasets. Use this as the validation core; **do not mark datasets fully certified** until real source metadata, file checksum, holiday/DST calendars and broker/session rules are integrated.

## Install

From repository root:

```bash
unzip -n ~/Downloads/tr02c-quality-engine.zip -d .
uv run pytest tests/trading/test_quality_validation.py -v
uv run pytest -q
```

## Example against imported CSV

```python
import csv
from app.trading.quality.validation import validate_candles, aggregate_h1_to_h4
with open('data/forex/historical_real/EURUSD_H1_2026-10-20_2026-10-21.csv', newline='') as f:
    candles = list(csv.DictReader(f))
report = validate_candles(candles, 'H1', '2026-10-20T00:00:00Z', '2026-10-21T00:00:00Z')
print(report)
if report.research_ready:
    h4 = aggregate_h1_to_h4(candles)
    print(h4)
```

## Next integration gate

Share the current `app/api/routes/trading_datasets.py`, catalogue service and `apps/web/app/trading/page.tsx` to add date filtering, quality display and H4 selections without overwriting working code. The weekend rule is an approximation; it cannot certify broker-specific holidays, DST, or real execution quality. Aggregation refuses partial four-hour buckets, including at session boundaries.
