from app.api.routes import trading_strategy as route

def test_missing_m15_fails_closed_when_h4_is_derived(monkeypatch):
    monkeypatch.setattr(
        route,
        "discover",
        lambda path: [{
            "id": "a",
            "instrument": "EURUSD",
            "timeframe": "H1",
            "data_kind": "historical_real",
            "source": "yahoo_finance",
            "quality_status": "coverage_pass_weekend_model_only",
            "count": 24,
            "last_timestamp": "2026-10-20T23:00:00Z",
        }],
    )

    result = route.analyse("EURUSD")

    assert result["decision"] == "NO_TRADE"
    assert set(result["missing_timeframes"]) == {"M15"}
    assert result["quality_certified"] is False

def test_even_three_uncertified_datasets_fail_closed(monkeypatch):
    monkeypatch.setattr(route, "discover", lambda path: [{"id":tf, "instrument":"EURUSD", "timeframe":tf, "data_kind":"historical_real", "source":"yahoo_finance", "quality_status":"coverage_pass_weekend_model_only", "count":250, "last_timestamp":"2026-10-20T23:00:00Z"} for tf in ("H4", "H1", "M15")])
    result = route.analyse("EURUSD")
    assert result["decision"] == "NO_TRADE"
    assert result["quality_certified"] is False
    assert result["missing_timeframes"] == []

def test_no_synthetic_datasets(monkeypatch):
    monkeypatch.setattr(route, "discover", lambda path: [{"id":"fake", "instrument":"EURUSD", "timeframe":"H4", "data_kind":"synthetic", "source":"local_csv", "quality_status":"certified_research_ready", "count":250, "last_timestamp":"2026-10-20T23:00:00Z"}])
    assert route.analyse("EURUSD")["datasets"] == {}
