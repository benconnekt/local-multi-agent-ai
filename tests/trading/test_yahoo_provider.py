from datetime import datetime, timezone
from unittest.mock import patch

import pandas as pd
import pytest

from app.trading.data.models import Instrument, Timeframe
from app.trading.data.providers.yahoo_provider import YahooDataError, YahooFinanceProvider, parse_yahoo_frame

UTC = timezone.utc
START = datetime(2026, 10, 20, tzinfo=UTC)
END = datetime(2026, 10, 21, tzinfo=UTC)


def frame():
    return pd.DataFrame(
        {"Open": [1.10, 1.11], "High": [1.12, 1.13],
         "Low": [1.09, 1.10], "Close": [1.11, 1.12]},
        index=pd.to_datetime(["2026-10-20T00:00:00Z", "2026-10-20T01:00:00Z"]),
    )


def test_parses_valid_ohlc():
    candles = parse_yahoo_frame(frame())
    assert len(candles) == 2
    assert candles[0].timestamp == START
    assert candles[1].close == 1.12
    assert candles[0].volume is None


def test_rejects_invalid_high():
    data = frame()
    data.loc[data.index[0], "High"] = 1.0
    with pytest.raises(YahooDataError, match="Invalid Yahoo candle"):
        parse_yahoo_frame(data)


def test_rejects_duplicate_timestamps():
    data = frame()
    data.index = pd.to_datetime(["2026-10-20T00:00:00Z"] * 2)
    with pytest.raises(YahooDataError, match="duplicates"):
        parse_yahoo_frame(data)


def test_rejects_unsupported_h4():
    with pytest.raises(YahooDataError, match="Unsupported"):
        YahooFinanceProvider().load(Instrument.EURUSD, Timeframe.H4, START, END)


def test_fetch_is_mockable_and_validated():
    with patch("yfinance.download", return_value=frame()) as download:
        candles = YahooFinanceProvider().load(Instrument.EURUSD, Timeframe.H1, START, END)
    assert len(candles) == 2
    assert download.call_args.args[0] == "EURUSD=X"
    assert download.call_args.kwargs["interval"] == "60m"
