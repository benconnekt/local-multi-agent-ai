"""Market-data and evidence-gated price-action research."""
from app.trading.agents.llm_research import explain_evidence


def market_data(state: dict) -> dict:
    context = state.get('verified_context') or {}
    evidence = context.get('price_action') or context.get('technical') or {}
    historical = (isinstance(evidence, dict) and evidence.get('data_kind') == 'historical_real'
                  and evidence.get('not_live') is True and evidence.get('quality_certified') is False)
    candles = state.get('candles') or []
    verified = state.get('market_data_verified') is True
    if historical:
        count = evidence.get('observations', 0)
        return {'findings': {'market_data': {
            'status': 'available_uncertified',
            'summary': f'{count} checksum-validated historical H1 observations; NOT LIVE, NOT quality-certified',
            'evidence_coverage': {'observations': count, 'timeframe': evidence.get('timeframe'),
                                  'last_observation_utc': evidence.get('last_observation_utc')},
            'quality_certified': False, 'not_live': True,
        }}}
    return {'findings': {'market_data': {
        'status': 'available' if candles and verified else 'unavailable',
        'summary': f'{len(candles)} externally validated observations supplied' if candles and verified
                   else 'No externally validated market observations supplied',
    }}}


def price_action(state: dict) -> dict:
    evidence = (state.get('verified_context') or {}).get('price_action')
    result = explain_evidence('price_action', state['instrument'], evidence)
    return {'findings': {'price_action': result}}
