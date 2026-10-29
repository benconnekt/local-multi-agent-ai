
from fastapi.testclient import TestClient

from app.api.main import app
from app.api.routes import trading
from app.trading.data.providers.csv_provider import CSVMarketDataProvider


def test_instruments_endpoint():
    with TestClient(app) as client:
        response = client.get("/api/v1/trading/instruments")

    assert response.status_code == 200
    body = response.json()
    assert len(body["instruments"]) == 3
    assert "H1" in body["timeframes"]


def test_candles_endpoint(tmp_path, monkeypatch):
    csv_file = tmp_path / "EURUSD_H1.csv"
    csv_file.write_text(
        "timestamp,open,high,low,close,volume\n"
        "2026-10-26T00:00:00Z,1.1625,1.1632,1.1619,1.1628,1250\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        trading,
        "get_provider",
        lambda: CSVMarketDataProvider(tmp_path),
    )

    with TestClient(app) as client:
        response = client.get(
            "/api/v1/trading/candles",
            params={"instrument": "EURUSD", "timeframe": "H1"},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 1
    assert body["source"] == "local_csv"
    assert body["data_kind"] == "synthetic"
    assert body["candles"][0]["close"] == 1.1628


def test_missing_dataset_returns_404(tmp_path, monkeypatch):
    monkeypatch.setattr(
        trading,
        "get_provider",
        lambda: CSVMarketDataProvider(tmp_path),
    )

    with TestClient(app) as client:
        response = client.get(
            "/api/v1/trading/candles",
            params={"instrument": "USDJPY", "timeframe": "D1"},
        )

    assert response.status_code == 404


def test_invalid_instrument_returns_422():
    with TestClient(app) as client:
        response = client.get(
            "/api/v1/trading/candles",
            params={"instrument": "INVALID", "timeframe": "H1"},
        )

    assert response.status_code == 422


def test_corrupted_dataset_returns_422(tmp_path, monkeypatch):
    (tmp_path / "EURUSD_H1.csv").write_text(
        "timestamp,open,high,low,close\n"
        "2026-10-26T00:00:00Z,1.2,1.0,1.1,1.2\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        trading,
        "get_provider",
        lambda: CSVMarketDataProvider(tmp_path),
    )

    with TestClient(app) as client:
        response = client.get(
            "/api/v1/trading/candles",
            params={"instrument": "EURUSD", "timeframe": "H1"},
        )

    assert response.status_code == 422
