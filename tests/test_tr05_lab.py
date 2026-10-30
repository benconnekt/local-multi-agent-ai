import pytest
from app.trading.research.intelligence_lab import indicator_evidence, ledger_diagnostics, research_overview

def test_safe_overview():
    report=research_overview()
    assert report['decision']=='NO_TRADE' and not report['broker_execution_enabled']
    assert not report['validation_pass']

def test_indicator_flat_closes():
    report=indicator_evidence([1.2]*30)
    assert report['rsi_14']==50.0
    assert report['decision']=='NO_TRADE'

def test_ledger_cost_and_drawdown():
    ledger=[{'signal_time_utc':'2026-01-01T00:00:00Z','outcome':'win','r_multiple':2},
            {'signal_time_utc':'2026-01-02T00:00:00Z','outcome':'loss','r_multiple':-1}]
    report=ledger_diagnostics(ledger,0.1)
    assert report['net_total_r']==pytest.approx(0.8)
    assert report['max_drawdown_r']==pytest.approx(1.1)
    assert report['sample_sufficient'] is False and report['validation_pass'] is False

def test_rejects_invalid_ledger():
    with pytest.raises(ValueError):
        ledger_diagnostics([{'signal_time_utc':'2026-01-01T00:00:00Z','outcome':'win','r_multiple':-1}])
