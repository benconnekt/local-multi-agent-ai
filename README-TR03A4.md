# TR-03A.4 — Safe scoring integration increment

This package is **additive**. It does not replace the current FastAPI strategy route, strategy evaluator, loader, or dashboard. The actual current versions of `app/api/routes/trading_strategy.py` and `app/trading/services/strategy_data_loader.py` were not supplied, so a fully wired market-evidence extractor cannot be validated safely.

## Install

From repository root:

```bash
unzip -n ~/Downloads/tr03a4-safe-integration.zip -d .
uv run pytest tests/trading/test_evidence_adapter.py -v
uv run pytest -q
```

Requires the existing `app/trading/scoring/opportunity.py` from TR-03A.3.

## Wire the API without changing existing fields

In `app/api/routes/trading_strategy.py`, import:

```python
from app.trading.scoring.evidence_adapter import evaluate_scoring
```

For an existing analysis result `report` (a dict), append the scoring object **after** determining the strategy decision, independently certified quality, and verified risk status:

```python
report["opportunity_score"] = evaluate_scoring(
    {},  # Until VERIFIED evidence extraction exists; never substitute invented strengths.
    strategy_decision=report["decision"],
    quality_certified=report["quality_certified"],
    risk_limits_passed=False,  # Until independently verified risk checks are exposed.
)
return report
```

This initial wiring correctly reports `UNRATED` and `NO_TRADE`. **Do not replace a strategy BUY/SELL with the scoring decision**, or use this placeholder as a finished evidence extraction pipeline. The score module is an advisory layer; the existing strategy decision remains authoritative, with risk gates enforced upstream.

## Wire the UI

In `StrategyResearchPanel.tsx`:

```tsx
import OpportunityScorecard, { type OpportunityScore } from "./OpportunityScorecard";
```

Add `opportunity_score?: OpportunityScore | null` to the `Report` type, and render within the `{report && <> ... </>}` block:

```tsx
<OpportunityScorecard score={report.opportunity_score} />
```

No changes to fetch URL or other existing report fields are necessary.

## What is still required to complete TR-03A.4

Supply the current `app/api/routes/trading_strategy.py`, `app/trading/services/strategy_data_loader.py`, and the indicator output shape of `evaluate(...)` or its current tests. We will map **verified** H4/H1/M15 features to scored factor strengths, with timestamp/provenance validation, and add route contract tests. Macro sentiment stays unavailable until its own evidence source is verified.

## Scoring semantics

The 5 factors must all have sourced strengths to publish a numeric score. An incomplete score remains `UNRATED`. A rating is not a probability of success. Missing data, uncertified quality, unverified risk, or underlying `NO_TRADE` cannot be bypassed by scoring.
