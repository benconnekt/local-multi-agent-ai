from app.trading.graphs.research_graph import run_research

def test_all_six_stage_findings_retained():
    for pair in ("EURUSD", "GBPUSD", "USDJPY"):
        result = run_research(pair)
        assert set(result["findings"]) == {"market_data", "price_action", "technical", "sentiment", "risk"}
        assert result["findings"]["market_data"]["status"] == "unavailable"
        assert result["report"]["findings"] == result["findings"]
        assert len(result["events"]) == 6
        assert result["report"]["decision"] == "NO_TRADE"
