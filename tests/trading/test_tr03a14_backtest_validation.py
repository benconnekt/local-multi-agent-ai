from copy import deepcopy
from app.trading.research.backtest_validation import audit_report


def report():
    return {'decision': 'NO_TRADE', 'research_only': True, 'quality_certified': False,
            'instrument': 'EURUSD', 'provider': 'oanda_v20', 'spread': .0002, 'slippage': 0,
            'simulated': 1, 'wins': 1, 'losses': 0, 'unresolved': 0,
            'win_rate': 1., 'expectancy_r': 1.9, 'total_r': 1.9, 'max_drawdown_r': 0.,
            'trades': [{'signal_time_utc': '2026-10-29T10:15:00+00:00',
                        'evidence': {'signal_close_utc': '2026-10-29T10:15:00+00:00',
                                     'h1_last_close_utc': '2026-10-29T10:00:00+00:00',
                                     'h4_last_close_utc': '2026-10-29T08:00:00+00:00'},
                        'simulation': {'outcome': 'win', 'r_multiple': 1.9,
                                       'entry_time_utc': '2026-10-29T10:15:00+00:00',
                                       'exit_time_utc': '2026-10-29T10:30:00+00:00'}}]}


def test_consistent_report():
    result = audit_report(report())
    assert result['audit_pass'] and result['decision'] == 'NO_TRADE'


def test_forged_total_fails():
    r = report(); r['total_r'] = 9
    assert not audit_report(r)['audit_pass']


def test_future_h4_fails():
    r = report(); r['trades'][0]['evidence']['h4_last_close_utc'] = '2026-10-29T12:00:00+00:00'
    assert any(x['code'] == 'future_h4_last_close_utc' for x in audit_report(r)['failures'])


def test_stale_h1_warns():
    r = report(); r['trades'][0]['evidence']['h1_last_close_utc'] = '2026-10-29T08:00:00+00:00'
    assert any(x['code'] == 'stale_h1_last_close_utc' for x in audit_report(r)['warnings'])


def test_rejects_unsafe_report():
    r = report(); r['decision'] = 'BUY'
    import pytest
    with pytest.raises(ValueError):
        audit_report(r)
