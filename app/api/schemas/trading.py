
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.trading.data.models import Instrument, Timeframe


class InstrumentInfo(BaseModel):
    symbol: Instrument
    display_name: str


class InstrumentsResponse(BaseModel):
    instruments: list[InstrumentInfo]
    timeframes: list[Timeframe]


class CandleResponse(BaseModel):
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float | None = None


class CandlesResponse(BaseModel):
    instrument: Instrument
    timeframe: Timeframe
    source: Literal["local_csv"]
    data_kind: Literal["synthetic"]
    count: int = Field(ge=0)
    candles: list[CandleResponse]
