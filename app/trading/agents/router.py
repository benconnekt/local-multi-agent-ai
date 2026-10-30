"""Read-only research operations with explicit non-executing run trigger."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.trading.agents.run_store import get_run, list_runs, start_run

router = APIRouter(prefix="/trading/agents", tags=["forex-agent-operations"])

class ForexAgent(BaseModel):
    id: str
    name: str
    role: str
    status: str = "available_for_research"
    capability: str

AGENTS = (
    ForexAgent(id="market_data", name="Market Data", role="Data validation", capability="Validate available market data and freshness"),
    ForexAgent(id="price_action", name="Price Action", role="Market structure", capability="Assess supplied price evidence"),
    ForexAgent(id="technical", name="Technical Analysis", role="Indicator research", capability="Evaluate supplied technical evidence"),
    ForexAgent(id="sentiment", name="News & Sentiment", role="Macro research", capability="Assess supplied macro evidence"),
    ForexAgent(id="risk", name="Risk Manager", role="Risk review", capability="Enforce research-only restrictions"),
    ForexAgent(id="supervisor", name="Trading Supervisor", role="Research coordination", capability="Consolidate research; never authorise execution"),
)

class ResearchRequest(BaseModel):
    instrument: str
    evidence_mode: str = "none"

@router.get("")
def list_forex_agents():
    return {"agents": [a.model_dump() for a in AGENTS], "total": len(AGENTS), "research_only": True, "decision": "NO_TRADE", "independently_certified": False}

@router.get("/activity")
def forex_agent_activity():
    events = [{**event, "id": f'{run["run_id"]}:{index}', "run_id": run["run_id"], "instrument": run["instrument"]} for run in list_runs() for index, event in enumerate(run["events"])]
    return {"events": events[:180], "source": "process_memory_non_durable", "decision": "NO_TRADE"}

@router.get("/readiness")
def forex_agent_readiness():
    return {"registry_ready": True, "orchestrator_connected": True, "event_store_connected": False, "activity_store": "process_memory_non_durable", "broker_execution_enabled": False, "research_only": True, "decision": "NO_TRADE", "quality_certified": False, "research_signal_eligible": False, "independently_certified": False}

@router.post("/runs", status_code=202)
def create_research_run(request: ResearchRequest):
    try:
        if request.evidence_mode not in {"none", "historical"}:
            raise ValueError("Unsupported evidence mode")
        return start_run(request.instrument, historical=request.evidence_mode == "historical")
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

@router.get("/runs")
def research_runs():
    return {"runs": list_runs(), "store": "process_memory_non_durable", "decision": "NO_TRADE"}

@router.get("/runs/{run_id}")
def research_run(run_id: str):
    run = get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return run

# Read-only practice monitoring; no broker order-changing endpoints.
from app.trading.broker.router import router as broker_monitor_router
router.include_router(broker_monitor_router)

# TR-05 research-only diagnostics (no broker mutations).
from app.trading.agents.lab_router import router as strategy_lab_router
router.include_router(strategy_lab_router)
