
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query

from app.api.schemas.trading import (
    CandlesResponse,
    CandleResponse,
    InstrumentsResponse,
    InstrumentInfo,
)
from app.trading.data.models import Instrument, Timeframe
from app.trading.data.providers.csv_provider import (
    CSVDataError,
    CSVMarketDataProvider,
)

router = APIRouter(prefix="/trading", tags=["trading"])

DATA_DIRECTORY = (
    Path(__file__).resolve().parents[3]
    / "data"
    / "forex"
    / "historical"
)


def get_provider() -> CSVMarketDataProvider:
    return CSVMarketDataProvider(DATA_DIRECTORY)


@router.get("/instruments", response_model=InstrumentsResponse)
def list_instruments() -> InstrumentsResponse:
    return InstrumentsResponse(
        instruments=[
            InstrumentInfo(
                symbol=Instrument.EURUSD,
                display_name="EUR/USD",
            ),
            InstrumentInfo(
                symbol=Instrument.GBPUSD,
                display_name="GBP/USD",
            ),
            InstrumentInfo(
                symbol=Instrument.USDJPY,
                display_name="USD/JPY",
            ),
        ],
        timeframes=list(Timeframe),
    )


@router.get("/candles", response_model=CandlesResponse)
def get_candles(
    instrument: Instrument = Query(...),
    timeframe: Timeframe = Query(...),
) -> CandlesResponse:
    try:
        candles = get_provider().load(instrument, timeframe)
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="Historical dataset not found",
        )
    except CSVDataError:
        raise HTTPException(
            status_code=422,
            detail="Historical dataset failed validation",
        )

    return CandlesResponse(
        instrument=instrument,
        timeframe=timeframe,
        source="local_csv",
        data_kind="synthetic",
        count=len(candles),
        candles=[
            CandleResponse.model_validate(candle.model_dump())
            for candle in candles
        ],
)
