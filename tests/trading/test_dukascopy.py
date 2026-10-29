from datetime import datetime, timezone, timedelta
import lzma
import struct
import pytest
from app.trading.data.providers.dukascopy import decode_bi5, aggregate, ImportErrorData

HOUR = datetime(2026, 10, 20, 9, tzinfo=timezone.utc)

def make_data(*records):
    return lzma.compress(b''.join(struct.pack('>IIIff', *record) for record in records))

def test_decoding_and_aggregation():
    data = make_data(
        (0, 110002, 110000, 1.0, 2.0),
        (900000, 110012, 110010, 1.0, 3.0),
        (1800000, 109992, 109990, 1.0, 4.0),
    )

    ticks = decode_bi5(data, HOUR, "EURUSD")
    candles = aggregate(ticks, 15)

    assert len(candles) == 3

    assert candles[0]["timestamp"] == "2026-10-20T09:00:00Z"
    assert candles[0]["open"] == 1.1000
    assert candles[0]["close"] == 1.1000

    assert candles[1]["timestamp"] == "2026-10-20T09:15:00Z"
    assert candles[1]["open"] == 1.1001
    assert candles[1]["close"] == 1.1001

    assert candles[2]["timestamp"] == "2026-10-20T09:30:00Z"
    assert candles[2]["open"] == 1.0999
    assert candles[2]["close"] == 1.0999

def test_reject_truncated():
    with pytest.raises(ImportErrorData, match='Truncated'):
        decode_bi5(lzma.compress(b'abc'), HOUR, 'EURUSD')

def test_reject_bad_order():
    data = make_data((1000, 110002, 110000, 1.0, 2.0), (0, 110002, 110000, 1.0, 2.0))
    with pytest.raises(ImportErrorData, match='Out-of-order'):
        decode_bi5(data, HOUR, 'EURUSD')

def test_reject_unsupported_symbol():
    with pytest.raises(ImportErrorData):
        decode_bi5(make_data(), HOUR, 'AUDUSD')
