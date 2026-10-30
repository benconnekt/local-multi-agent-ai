from datetime import datetime, timezone, timedelta
import pytest
from app.trading.research.backtest import Bar, Hypothesis, simulate
T = datetime(2026, 10, 30, 8, tzinfo=timezone.utc)
def bar(n, o=100, h=101, l=99, c=100):
    return Bar(T+timedelta(minutes=15*n),o,h,l,c)
def test_long_win():
    x=simulate([bar(1,100,103,100,102)],Hypothesis('LONG',T,1))
    assert x['outcome']=='win' and x['r_multiple']==2 and x['decision']=='NO_TRADE'
def test_stop_first_when_both_hit():
    x=simulate([bar(1,100,103,98,100)],Hypothesis('LONG',T,1))
    assert x['outcome']=='loss' and x['ambiguity_stop_first']
def test_short_win():
    x=simulate([bar(1,100,100,97,98)],Hypothesis('SHORT',T,1))
    assert x['outcome']=='win'
def test_no_future():
    assert simulate([bar(-1)],Hypothesis('LONG',T,1))['outcome']=='unresolved'
def test_costs_reduce_r():
    x=simulate([bar(1,100,103,100,102)],Hypothesis('LONG',T,1),spread=.1,slippage=.01)
    assert x['r_multiple']<2
def test_risk_cap():
    with pytest.raises(ValueError):simulate([bar(1)],Hypothesis('LONG',T,1),risk_fraction=.01)
def test_duplicate_rejected():
    with pytest.raises(ValueError):simulate([bar(1),bar(1)],Hypothesis('LONG',T,1))
def test_naive_time_rejected():
    with pytest.raises(ValueError):simulate([bar(1)],Hypothesis('LONG',datetime(2026,10,30),1))
