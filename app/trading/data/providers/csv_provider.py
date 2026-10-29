
import csv
from pathlib import Path

from app.trading.data.models import Candle, Instrument, Timeframe


class CSVDataError(ValueError):
    pass


class CSVMarketDataProvider:
    def __init__(self, data_directory: Path):
        self.data_directory = Path(data_directory)

    def load(
        self,
        instrument: Instrument,
        timeframe: Timeframe,
    ) -> list[Candle]:
        filename = f"{instrument.value}_{timeframe.value}.csv"
        path = self.data_directory / filename

        if not path.is_file():
            raise FileNotFoundError(
                f"Historical market data not found: {filename}"
            )

        candles: list[Candle] = []
        previous_timestamp = None

        with path.open("r", encoding="utf-8-sig", newline="") as file:
            reader = csv.DictReader(file)

            required = {
                "timestamp", "open", "high", "low", "close"
            }

            if not reader.fieldnames or not required.issubset(
                set(reader.fieldnames)
            ):
                raise CSVDataError(
                    f"{filename}: missing required CSV columns"
                )

            for row_number, row in enumerate(reader, start=2):
                try:
                    if None in row:
                        raise ValueError("Unexpected extra CSV fields")

                    timestamp = row["timestamp"]
                    if not timestamp:
                        raise ValueError("Missing timestamp")

                    candle = Candle(
                        timestamp=timestamp,
                        open=row["open"],
                        high=row["high"],
                        low=row["low"],
                        close=row["close"],
                        volume=(
                            row.get("volume")
                            if row.get("volume") not in ("", None)
                            else None
                        ),
                    )

                    if (
                        previous_timestamp is not None
                        and candle.timestamp <= previous_timestamp
                    ):
                        raise ValueError(
                            "Duplicate or unsorted candle timestamp"
                        )

                    candles.append(candle)
                    previous_timestamp = candle.timestamp

                except (ValueError, TypeError) as exc:
                    raise CSVDataError(
                        f"{filename}, row {row_number}: {exc}"
                    ) from exc

        if not candles:
            raise CSVDataError(f"{filename}: no candles found")

        return candles
