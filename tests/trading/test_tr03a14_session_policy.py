from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
import pytest
from app.trading.research.session_policy import entry_allowed, evidence_fresh, is_weekend_hold
from app.trading.research.backtest import Bar, Hypothesis, simulate
from app.trading.research.historical_runner import BASE
NY = ZoneInfo('America/New_York')
def ny(y,m,d,h,minute=0): return datetime(y,m,d,h,minute,tzinfo=NY)
@pytest.mark.parametrize('stamp,allowed', [
 (ny(2026,10,30,15,45),True),(ny(2026,10,30,16),False),
 (ny(2026,10,31,12),False),(ny(2026,11,1,18),False),
 (ny(2026,11,2,0,45),False),(ny(2026,11,2,1),True),
 (ny(2026,3,6,16),False),(ny(2026,3,9,1),True),
])
def test_entry_policy(stamp,allowed): assert entry_allowed(stamp)==allowed

def test_friday_boundary_dst():
 assert is_weekend_hold(ny(2026,10,30,15),ny(2026,11,2,1))
 assert is_weekend_hold(ny(2026,3,6,15),ny(2026,3,9,1))
 assert not is_weekend_hold(ny(2026,10,30,14),ny(2026,10,30,15))

def test_weekend_reopen_stop_gap_long():
 signal=ny(2026,10,30,15,45).astimezone(timezone.utc)
 bars=[Bar(signal,1.1000,1.1010,1.0990,1.1000),
       Bar(ny(2026,11,1,17).astimezone(timezone.utc),1.0800,1.0850,1.0750,1.0800)]
 result=simulate(bars,Hypothesis('LONG',signal,0.01))
 assert result['outcome']=='loss'
 assert result['exit']==pytest.approx(1.08)
 assert result['r_multiple']==pytest.approx(-2)

def test_weekend_reopen_target_no_positive_gap_improvement():
 signal=ny(2026,10,30,15,45).astimezone(timezone.utc)
 bars=[Bar(signal,1.1,1.101,1.099,1.1),
       Bar(ny(2026,11,1,17).astimezone(timezone.utc),1.15,1.16,1.14,1.15)]
 result=simulate(bars,Hypothesis('LONG',signal,0.01))
 assert result['outcome']=='win'
 assert result['exit']==pytest.approx(1.12)

def test_future_evidence_rejected():
 with pytest.raises(ValueError):
  evidence_fresh({'h4_last_close_utc':ny(2026,11,2,3).isoformat(),
                  'h1_last_close_utc':ny(2026,11,2,1).isoformat()},ny(2026,11,2,1))

def test_fail_closed():
 assert BASE['decision']=='NO_TRADE'
 assert BASE['research_only'] and not BASE['quality_certified'] and not BASE['research_signal_eligible']

def test_naive_rejected():
 with pytest.raises(ValueError): entry_allowed(datetime(2026,10,30,15))
