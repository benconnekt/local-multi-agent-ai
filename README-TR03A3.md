# TR-03A.3 — Opportunity Scoring & Explainability (isolated module)

This package adds `app/trading/scoring/` and `tests/trading/test_opportunity_scoring.py` only. It does **not** modify existing strategy, API, frontend, dataset files or risk policies.

## Install
From the repository root:

```bash
unzip -n ~/Downloads/tr03a3-scoring-engine.zip -d .
uv run pytest tests/trading/test_opportunity_scoring.py -v
uv run pytest -q
```

## API / frontend integration
Not included in this increment. The current `trading_strategy.analyse()` endpoint is still fail-closed and does not supply five verified factor inputs. **Do not generate fake strengths or set `quality_certified=True` just to obtain a rating.** Integrate the scoring service only after the strategy evaluation and evidence-provenance pipeline is complete.

Example using deliberately illustrative test evidence:

```python
from app.trading.scoring import FactorEvidence, score_opportunity
from app.trading.scoring.opportunity import WEIGHTS

evidence = {
    name: FactorEvidence(0.8, "Illustrative test evidence", "synthetic_test")
    for name in WEIGHTS
}
result = score_opportunity(
    evidence,
    strategy_decision="NO_TRADE",
    quality_certified=False,
    risk_limits_passed=False,
)
print(result.to_dict())  # 80/B but NO_TRADE, never eligible
```

## Semantics
- Scores are *heuristic confluence strength*, **not** win probability or financial advice.
- Factors: structure 25, price action 25, alignment 20, momentum/volatility 15, macro/sentiment 15.
- Missing factor => `score: null`, `rating: UNRATED`, `decision: NO_TRADE`.
- Rating boundaries: A >= 85; B >= 70; C >= 55; D < 55.
- Quality, risk and strategy decision are hard gates. A high score never bypasses them.
- Scoring does not place trades or execute orders.
- Factor strengths must come from future deterministic feature extractors and traceable sources, not an LLM's unsupported confidence claims.
