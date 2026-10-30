from unittest.mock import patch
from app.trading.broker.oanda_monitor import snapshot

def test_unconfigured(monkeypatch):
    monkeypatch.setenv("OANDA_ENVIRONMENT", "practice")
    monkeypatch.delenv("OANDA_API_TOKEN", raising=False)
    monkeypatch.delenv("OANDA_ACCOUNT_ID", raising=False)
    assert snapshot()["status"] == "not_configured"

def test_live_environment_blocked(monkeypatch):
    monkeypatch.setenv("OANDA_ENVIRONMENT", "live")
    assert snapshot()["status"] == "disabled"

def test_practice_read_only(monkeypatch):
    monkeypatch.setenv("OANDA_ENVIRONMENT", "practice")
    monkeypatch.setenv("OANDA_API_TOKEN", "dummy")
    monkeypatch.setenv("OANDA_ACCOUNT_ID", "101-001-1234567-001")
    from app.trading.broker import oanda_monitor
    def fake(path, **kwargs):
        if path == "summary": return {"account": {"currency": "GBP", "balance": "1000"}}
        if path == "openTrades": return {"trades": [{"id":"123","instrument":"EUR_USD","currentUnits":"100"}]}
        if path == "openPositions": return {"positions": []}
        raise AssertionError(path)
    with patch.object(oanda_monitor, "_request", side_effect=fake) as mock:
        result = snapshot()
    assert result["status"] == "connected"
    assert result["broker_execution_enabled"] is False
    assert result["trades"][0]["id"] == "123"
    assert mock.call_count == 3
    assert "dummy" not in str(result)
