"""Explicit broker-observed candle absences; not evidence of a market closure."""
from datetime import datetime, timezone

GBPUSD_M15_2025_12_21_2215 = datetime(2025, 12, 21, 22, 15, tzinfo=timezone.utc)
BROKER_OBSERVED_ABSENCES_V1 = {
    ("oanda_v20", "GBPUSD", "M15"): frozenset({GBPUSD_M15_2025_12_21_2215}),
}
EVIDENCE = {
    "source": "OANDA v20 practice GET /v3/instruments/GBP_USD/candles",
    "window_utc": "2025-12-21T22:00:00Z/2025-12-21T23:00:00Z",
    "observed_candles_utc": ["2025-12-21T22:00:00Z", "2025-12-21T22:30:00Z", "2025-12-21T22:45:00Z"],
    "absent_candle_utc": "2025-12-21T22:15:00Z",
    "classification": "BROKER_CONFIRMED_ABSENT_CANDLE",
    "market_closed_verified": False,
    "independently_certified": False,
}
