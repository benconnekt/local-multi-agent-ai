
import pytest

from app.trading.data.models import Instrument, Timeframe
from app.trading.data.providers.csv_provider import (
    CSVDataError,
    CSVMarketDataProvider,
)


HEADER = "timestamp,open,high,low,close,volume\n"

VALID_ROW = (
    "2026-10-26T00:00:00Z,"
    "1.16250,1.16320,1.16190,1.16280,1250\n"
)


def write_csv(tmp_path, contents):
    path = tmp_path / "EURUSD_H1.csv"
    path.write_text(contents, encoding="utf-8")
    return CSVMarketDataProvider(tmp_path)


def test_load_valid_candles(tmp_path):
    provider = write_csv(tmp_path, HEADER + VALID_ROW)

    candles = provider.load(Instrument.EURUSD, Timeframe.H1)

    assert len(candles) == 1
    assert candles[0].close == 1.16280
    assert candles[0].volume == 1250


def test_reject_duplicate_timestamps(tmp_path):
    provider = write_csv(
        tmp_path,
        HEADER + VALID_ROW + VALID_ROW,
    )

    with pytest.raises(CSVDataError, match="Duplicate"):
        provider.load(Instrument.EURUSD, Timeframe.H1)


def test_reject_invalid_ohlc(tmp_path):
    provider = write_csv(
        tmp_path,
        HEADER
        + "2026-10-26T00:00:00Z,"
        + "1.16250,1.16000,1.16190,1.16280,1250\n",
    )

    with pytest.raises(CSVDataError):
        provider.load(Instrument.EURUSD, Timeframe.H1)


def test_reject_missing_columns(tmp_path):
    provider = write_csv(
        tmp_path,
        "timestamp,open,close\n"
        "2026-10-26T00:00:00Z,1.1,1.2\n",
    )

    with pytest.raises(CSVDataError, match="missing required"):
        provider.load(Instrument.EURUSD, Timeframe.H1)


def test_reject_unsorted_timestamps(tmp_path):
    provider = write_csv(
        tmp_path,
        HEADER
        + VALID_ROW
        + "2026-10-25T23:00:00Z,"
        + "1.16250,1.16320,1.16190,1.16280,1250\n",
    )

    with pytest.raises(CSVDataError, match="unsorted"):
        provider.load(Instrument.EURUSD, Timeframe.H1)


def test_missing_file(tmp_path):
    provider = CSVMarketDataProvider(tmp_path)

    with pytest.raises(FileNotFoundError):
        provider.load(Instrument.GBPUSD, Timeframe.D1)
