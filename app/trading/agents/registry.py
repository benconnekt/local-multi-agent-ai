"""Forex research workflow agent identities; separate from software agents."""
AGENT_ROLES = {
    "market_data": "Market Data",
    "price_action": "Price Action",
    "technical": "Technical Analysis",
    "sentiment": "News & Sentiment",
    "risk": "Risk Manager",
    "supervisor": "Trading Supervisor",
}
INSTRUMENTS = frozenset({"EURUSD", "GBPUSD", "USDJPY"})
