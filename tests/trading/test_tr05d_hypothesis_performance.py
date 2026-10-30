from datetime import datetime, timedelta, timezone
from app.trading.research.backtest import Bar
from app.trading.research.hypothesis_generator import (
    _ema, _ema_prefix, _h4_from_h1, _complete_h4, discover_hypotheses,
)

T = datetime(2025, 1, 6, tzinfo=timezone.utc)


def test_ema_prefix_matches_reference_at_every_cutoff():
    closes = [1.0 + i * 0.0001 + (i % 7) * 0.001 for i in range(300)]
    for period in (20, 50, 200):
        prefix = _ema_prefix(closes, period)
        for i in range(len(closes)):
            assert prefix[i] == _ema(closes[:i + 1], period)


def test_h4_complete_matches_reference_for_gapped_history():
    rows = [Bar(T + timedelta(hours=i), 1.1, 1.2, 1.0, 1.15)
            for i in range(80) if i not in (13, 14, 55)]
    assert _complete_h4(rows) == _h4_from_h1(rows, T + timedelta(hours=80))


def test_no_lookahead_with_optimised_history():
    h1 = [Bar(T + timedelta(hours=i), 1.1, 1.2, 1.0, 1.15) for i in range(1100)]
    m15 = [Bar(T + timedelta(minutes=15*i), 1.1, 1.2, 1.0, 1.15) for i in range(4400)]
    cutoff = T + timedelta(hours=1050)
    first = discover_hypotheses(h1, m15, as_of=cutoff)
    future = Bar(T + timedelta(hours=1200), 1.5, 1.6, 1.4, 1.55)
    second = discover_hypotheses(h1 + [future], m15 + [future], as_of=cutoff)
    assert first == second
    assert first['decision'] == 'NO_TRADE'
