"""Read-only OANDA practice monitor. No order-changing HTTP methods."""
import json
import os
import re
import urllib.error
import urllib.request
from decimal import Decimal, InvalidOperation

HOST = "https://api-fxpractice.oanda.com"
ACCOUNT_RE = re.compile(r"^[0-9-]{3,64}$")

def _request(path: str, *, token: str, account_id: str) -> dict:
    if not ACCOUNT_RE.fullmatch(account_id):
        raise ValueError("Invalid OANDA practice account ID")
    req = urllib.request.Request(
        f"{HOST}/v3/accounts/{account_id}/{path}",
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=8) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"OANDA returned HTTP {exc.code}") from None
    except (urllib.error.URLError, TimeoutError):
        raise RuntimeError("OANDA practice account temporarily unreachable") from None

def snapshot() -> dict:
    if os.getenv("OANDA_ENVIRONMENT", "practice").strip().lower() != "practice":
        return {"status": "disabled", "environment": "practice", "reason": "Only practice monitoring is permitted", "broker_execution_enabled": False}
    token = os.getenv("OANDA_API_TOKEN", "").strip()
    account_id = os.getenv("OANDA_ACCOUNT_ID", "").strip()
    if not token or not account_id:
        return {"status": "not_configured", "environment": "practice", "reason": "Set OANDA_API_TOKEN and OANDA_ACCOUNT_ID locally", "broker_execution_enabled": False}
    summary = _request("summary", token=token, account_id=account_id).get("account")
    trades = _request("openTrades", token=token, account_id=account_id).get("trades")
    positions = _request("openPositions", token=token, account_id=account_id).get("positions")
    if not isinstance(summary, dict) or not isinstance(trades, list) or not isinstance(positions, list):
        raise RuntimeError("Unexpected OANDA response structure")
    return {
        "status": "connected", "environment": "practice", "source": "oanda_practice_api",
        "account_id_masked": "••••" + account_id[-4:],
        "broker_execution_enabled": False, "research_only": True,
        "account": {k: summary.get(k) for k in ("currency", "balance", "NAV", "unrealizedPL", "marginAvailable", "marginUsed", "openTradeCount")},
        "trades": [{k: t.get(k) for k in ("id", "instrument", "currentUnits", "price", "unrealizedPL", "openTime", "stopLossOrder", "takeProfitOrder")} for t in trades],
        "positions": [{k: p.get(k) for k in ("instrument", "long", "short", "unrealizedPL")} for p in positions],
        "trade_explanations_available": False,
    }
