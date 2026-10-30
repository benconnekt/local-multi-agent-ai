from datetime import datetime, timedelta, timezone
import pytest
from app.trading.research.backtest import Bar
from app.trading.research.hypothesis_generator import discover_hypotheses, _h4_from_h1

T = datetime(2026, 1, 5, tzinfo=timezone.utc)

def bars(n, step, start=T):
    return [Bar(start + i * step, 1.2, 1.3, 1.1, 1.2) for i in range(n)]

def test_no_h4_warmup_does_not_generate():
    result = discover_hypotheses(bars(8, timedelta(hours=1)), bars(20, timedelta(minutes=15)), as_of=T+timedelta(hours=9))
    assert result['hypotheses'] == []
    assert result['decision'] == 'NO_TRADE'
    assert result['research_signal_eligible'] is False

def test_future_bars_do_not_affect_past():
    h1 = bars(12, timedelta(hours=1))
    m15 = bars(20, timedelta(minutes=15))
    cutoff = T+timedelta(hours=3)
    first = discover_hypotheses(h1, m15, as_of=cutoff)
    extra = Bar(T+timedelta(days=2), 9, 10, 8, 9)
    second = discover_hypotheses(h1+[extra], m15+[extra], as_of=cutoff)
    assert first['hypotheses'] == second['hypotheses']
    assert first['rejected_counts'] == second['rejected_counts']

def test_incomplete_h4_excluded():
    assert len(_h4_from_h1(bars(3, timedelta(hours=1)), T+timedelta(hours=4))) == 0
    assert len(_h4_from_h1(bars(4, timedelta(hours=1)), T+timedelta(hours=4))) == 1

def test_duplicate_rejected():
    with pytest.raises(ValueError, match='Duplicate'):
        discover_hypotheses([], [bars(1, timedelta(minutes=15))[0]]*2, as_of=T)

def test_naive_as_of_rejected():
    with pytest.raises(ValueError, match='Timezone-aware'):
        discover_hypotheses([], [], as_of=datetime(2026,1,5))

def test_bad_reward_to_risk_rejected():
    with pytest.raises(ValueError, match='reward/risk'):
        discover_hypotheses([], [], as_of=T, reward_to_risk=1.5)
