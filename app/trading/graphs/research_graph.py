"""Auditable Forex research graph. AI commentary is never trade authorization."""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Annotated, Any, TypedDict
from operator import add
from uuid import uuid4
from time import monotonic
from langgraph.graph import END, START, StateGraph
from app.trading.agents.registry import INSTRUMENTS
from app.trading.agents.market_analyst import market_data, price_action
from app.trading.agents.strategy_analyst import technical_analysis
from app.trading.agents.macro_analyst import sentiment_analysis
from app.trading.agents.risk_analyst import risk_review


def merge_findings(left: dict, right: dict) -> dict:
    return {**left, **right}


class ResearchState(TypedDict, total=False):
    run_id: str
    instrument: str
    candles: list[dict]
    market_data_verified: bool
    verified_context: dict[str, dict[str, Any]]
    findings: Annotated[dict[str, dict[str, Any]], merge_findings]
    events: Annotated[list[dict[str, Any]], add]
    report: dict


def _stage(agent_id: str, function):
    def node(state: ResearchState) -> dict:
        start = monotonic()
        try:
            output = function(state)
        except Exception as exc:
            output = {'findings': {agent_id: {'status': 'failed', 'summary': f'Stage failed: {type(exc).__name__}'}}}
        finding = output['findings'][agent_id]
        return {**output, 'events': [{
            'agent_id': agent_id,
            'status': finding['status'],
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'duration_ms': round((monotonic() - start) * 1000),
            'summary': finding['summary'],
            'event_id': f"{state['run_id']}:{agent_id}",
            'duration_source': 'monotonic_wall_clock',
        }]}
    return node


def supervisor(state: ResearchState) -> dict:
    findings = state.get('findings', {})
    return {'report': {
        'run_id': state['run_id'], 'instrument': state['instrument'],
        'findings': findings, 'decision': 'NO_TRADE', 'research_only': True,
        'quality_certified': False, 'research_signal_eligible': False,
        'independently_certified': False, 'broker_execution_enabled': False,
    }, 'events': [{
        'agent_id': 'supervisor', 'status': 'completed',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'duration_ms': 0, 'summary': 'Uncertified research consolidated; NO_TRADE enforced',
        'event_id': f"{state['run_id']}:supervisor", 'duration_source': 'not_measured',
    }]}


builder = StateGraph(ResearchState)
for name, fn in (
    ('market_data', market_data), ('price_action', price_action),
    ('technical', technical_analysis), ('sentiment', sentiment_analysis),
    ('risk', risk_review),
):
    builder.add_node(name, _stage(name, fn))
builder.add_node('supervisor', supervisor)
for a, b in zip(
    (START, 'market_data', 'price_action', 'technical', 'sentiment', 'risk', 'supervisor'),
    ('market_data', 'price_action', 'technical', 'sentiment', 'risk', 'supervisor', END),
):
    builder.add_edge(a, b)
research_graph = builder.compile()


def run_research(instrument: str, *, verified_context: dict | None = None) -> ResearchState:
    """Run research. Context must be validated by caller; never use as trading signals.

    No implicit data import or broker access. No-context runs never call Ollama.
    """
    if instrument not in INSTRUMENTS:
        raise ValueError('Unsupported instrument')
    if verified_context is not None and not isinstance(verified_context, dict):
        raise ValueError('verified_context must be a dictionary')
    if verified_context and (set(verified_context) - {'price_action', 'technical', 'sentiment'}):
        raise ValueError('Unknown evidence category')
    return research_graph.invoke({
        'run_id': str(uuid4()), 'instrument': instrument,
        'candles': [], 'market_data_verified': False,
        'verified_context': verified_context or {}, 'findings': {}, 'events': [],
    })
