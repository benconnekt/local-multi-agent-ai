from copy import deepcopy
from datetime import datetime, timezone
from app.trading.research.trade_ledger import build_trade_ledger

UTC = timezone.utc

def report():
    return {
        'decision': 'NO_TRADE', 'research_only': True, 'quality_certified': False,
        'research_signal_eligible': False, 'independently_certified': False,
        'hypothetical': True, 'instrument': 'EURUSD', 'provider': 'oanda_v20',
        'as_of_utc': '2026-10-29T16:00:00+00:00', 'dataset_ids': {'H1':['a'],'M15':['b']},
        'spread': 0.0002, 'slippage': 0.0001, 'risk_fraction': 0.005,
        'session_policy': 'NY', 'generated_hypotheses': 1, 'simulated': 1,
        'skipped_counts': {}, 'weekend_holds': 0, 'wins': 1, 'losses': 0,
        'unresolved': 0, 'win_rate': 1., 'expectancy_r': 2., 'total_r': 2.,
        'max_drawdown_r': 0.,
        'trades': [{'signal_time_utc': '2026-10-29T15:00:00+00:00', 'direction':'LONG',
          'evidence': {'signal_close_utc':'2026-10-29T15:00:00+00:00',
                       'h1_last_close_utc':'2026-10-29T15:00:00+00:00',
                       'h4_last_close_utc':'2026-10-29T12:00:00+00:00'},
          'simulation': {'decision':'NO_TRADE', 'outcome':'win',
              'entry_time_utc':'2026-10-29T15:00:00+00:00',
              'exit_time_utc':'2026-10-29T15:15:00+00:00',
              'entry':1.1, 'stop':1.09, 'target':1.12, 'exit':1.12,
              'r_multiple':2.0}}]}

def test_valid_ledger():
    result = build_trade_ledger(report())
    assert result['audit_pass'], result['failures']
    assert len(result['ledger_sha256']) == 64
    assert result['decision'] == 'NO_TRADE'

def test_tampered_r_rejected():
    r = report()
    r['trades'][0]['simulation']['r_multiple'] = 3.
    assert not build_trade_ledger(r)['audit_pass']

def test_unsafe_flags_rejected():
    r = report()
    r['decision'] = 'BUY'
    import pytest
    with pytest.raises(ValueError):
        build_trade_ledger(r)

def test_reproducible_digest():
    assert build_trade_ledger(report())['ledger_sha256'] == build_trade_ledger(deepcopy(report()))['ledger_sha256']

def test_weekend_entry_rejected():
    r = report()
    r['trades'][0]['signal_time_utc'] = '2026-10-31T15:00:00+00:00'
    assert not build_trade_ledger(r)['audit_pass']
