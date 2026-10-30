from fastapi import APIRouter, HTTPException
from app.trading.broker.oanda_monitor import snapshot

router = APIRouter()

@router.get("/broker/overview")
def broker_overview():
    try:
        return snapshot()
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
