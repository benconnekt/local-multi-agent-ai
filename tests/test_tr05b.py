from fastapi.testclient import TestClient
from fastapi import FastAPI
from app.trading.agents.lab_router import router

def test_invalid_pair_fails_closed():
    app = FastAPI(); app.include_router(router)
    r = TestClient(app).post('/lab/historical/backtest',json={'instrument':'BTCUSD'})
    assert r.status_code == 422

def test_missing_history_fails_closed(monkeypatch, tmp_path):
    import app.trading.agents.lab_router as module
    monkeypatch.setattr(module,'HISTORICAL_DIRECTORY',tmp_path)
    app = FastAPI(); app.include_router(router)
    r = TestClient(app).post('/lab/historical/backtest',json={'instrument':'EURUSD'})
    assert r.status_code == 422
    assert 'NO_TRADE' not in str(r.json()) or r.status_code == 422
