"""Evidence-gated macro commentary; no news source is invented."""
from app.trading.agents.llm_research import explain_evidence


def sentiment_analysis(state: dict) -> dict:
    evidence = (state.get('verified_context') or {}).get('sentiment')
    return {'findings': {'sentiment': explain_evidence('sentiment', state['instrument'], evidence)}}
