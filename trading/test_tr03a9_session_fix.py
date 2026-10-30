from datetime import datetime, timezone
from app.trading.quality.fx_session_validation import _market_open
from app.trading.quality.readiness_report import build_session_readiness


def test_new_york_dst_boundaries():
    def utc(s): return datetime.fromisoformat(s).replace(tzinfo=timezone.utc)
    assert _market_open(utc('2026-07-05T21:00:00'))
    assert not _market_open(utc('2026-07-05T20:00:00'))
    assert _market_open(utc('2026-01-04T22:00:00'))
    assert not _market_open(utc('2026-01-04T21:00:00'))
    assert not _market_open(utc('2026-07-03T21:00:00'))


def test_identical_overlaps_are_reconciled():
    row = {'timestamp': '2026-10-26T12:00:00+00:00', 'open': 1.1, 'high': 1.2, 'low': 1.0, 'close': 1.15, 'volume': 10}
    entries = [{'source': 'oanda_v20', 'timeframe': 'H1', 'candles': [row]},
               {'source': 'oanda_v20', 'timeframe': 'H1', 'candles': [dict(row)]}]
    report = build_session_readiness(entries)
    assert report['H1']['candle_count'] == 1
    assert report['H1']['duplicate_timestamps'] == 0
    assert report['research_signal_eligible'] is False


def test_mixed_providers_require_selection():
    entries = [{'source': p, 'timeframe': 'H1', 'candles': []} for p in ('oanda_v20', 'yahoo_finance')]
    assert build_session_readiness(entries)['status'] == 'provider_selection_required'
    assert build_session_readiness(entries, provider='oanda_v20')['provider'] == 'oanda_v20'


def test_conflicting_overlaps_fail_closed():
    row = {'timestamp': '2026-10-26T12:00:00+00:00', 'open': 1.1, 'high': 1.2, 'low': 1.0, 'close': 1.15, 'volume': 10}
    other = {**row, 'close': 1.16}
    entries = [{'source': 'oanda_v20', 'timeframe': 'H1', 'candles': [row, other]}]
    report = build_session_readiness(entries)
    assert report['H1']['status'] == 'conflicting_overlaps'
    assert report['H4']['complete_candles'] == 0
