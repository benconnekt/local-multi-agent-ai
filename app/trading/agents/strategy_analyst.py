"""Evidence-gated technical commentary; no indicators calculated by LLM."""
from app.trading.agents.llm_research import explain_evidence


def technical_analysis(state: dict) -> dict:
    evidence = (state.get('verified_context') or {}).get('technical')
    return {'findings': {'technical': explain_evidence('technical', state['instrument'], evidence)}}
