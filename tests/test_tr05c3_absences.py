from datetime import datetime, timedelta, timezone
from app.trading.quality.fx_session_validation import audit_sessions
from app.trading.quality.broker_absences import BROKER_OBSERVED_ABSENCES_V1, GBPUSD_M15_2025_12_21_2215

def test_broker_absence_is_explicit_and_does_not_fabricate():
    ts = GBPUSD_M15_2025_12_21_2215
    def bar(t): return dict(timestamp=t, open=1.3, high=1.31, low=1.29, close=1.3)
    rows = [bar(ts-timedelta(minutes=15)), bar(ts+timedelta(minutes=15))]
    ordinary = audit_sessions(rows, 'M15')
    assert ordinary.missing_expected_candles == 1
    allowed = audit_sessions(rows, 'M15', acknowledged_absences=BROKER_OBSERVED_ABSENCES_V1['oanda_v20','GBPUSD','M15'])
    assert allowed.provisional_schedule_pass
    assert allowed.missing_expected_candles == 0
    assert allowed.acknowledged_absence_intervals == 1
    assert allowed.candle_count == 2

def test_no_unlisted_absences_accepted():
    ts = GBPUSD_M15_2025_12_21_2215
    def bar(t): return dict(timestamp=t, open=1.3, high=1.31, low=1.29, close=1.3)
    rows = [bar(ts-timedelta(minutes=15)), bar(ts+timedelta(minutes=30))]
    result = audit_sessions(rows, 'M15', acknowledged_absences=BROKER_OBSERVED_ABSENCES_V1['oanda_v20','GBPUSD','M15'])
    assert result.missing_expected_candles == 1
    assert not result.provisional_schedule_pass
