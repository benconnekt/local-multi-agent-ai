import json
import pytest
from app.trading.agents.llm_research import explain_evidence
from app.trading.graphs.research_graph import run_research


class StubResponse:
    def __init__(self, content): self.content = content


class StubLLM:
    def __init__(self, content=None, error=None):
        self.content, self.error, self.calls = content, error, 0
    def invoke(self, prompt):
        self.calls += 1
        if self.error: raise self.error
        return StubResponse(self.content)


def test_no_context_never_invokes_llm():
    for pair in ('EURUSD', 'GBPUSD', 'USDJPY'):
        state = run_research(pair)
        assert len(state['events']) == 6
        assert set(state['findings']) == {'market_data', 'price_action', 'technical', 'sentiment', 'risk'}
        assert all(state['findings'][key]['status'] == 'unavailable' for key in ('price_action', 'technical', 'sentiment'))
        assert state['report']['decision'] == 'NO_TRADE'


def test_valid_evidence_gets_commentary():
    llm = StubLLM(json.dumps({'summary': 'The supplied indicator is neutral; no inference about direction is justified.'}))
    result = explain_evidence('technical', 'EURUSD', {'rsi': 50}, llm=llm)
    assert result['status'] == 'commentary_unverified'
    assert result['llm_used'] is True
    assert llm.calls == 1


def test_missing_evidence_does_not_call_llm():
    llm = StubLLM('{}')
    assert explain_evidence('technical', 'EURUSD', {}, llm=llm)['status'] == 'unavailable'
    assert llm.calls == 0


@pytest.mark.parametrize('bad', ['not json', '{"summary": 12}', '{"summary": ""}'])
def test_invalid_llm_response_fails_closed(bad):
    assert explain_evidence('technical', 'EURUSD', {'rsi': 50}, llm=StubLLM(bad))['status'] == 'failed'


def test_llm_error_fails_closed():
    assert explain_evidence('sentiment', 'USDJPY', {'event': 'verified'}, llm=StubLLM(error=TimeoutError()))['status'] == 'failed'


def test_context_categories_restricted():
    with pytest.raises(ValueError):
        run_research('EURUSD', verified_context={'orders': {'execute': True}})
