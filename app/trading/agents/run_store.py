"""Process-local bounded research run store; deliberately not persistent."""
from __future__ import annotations
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from threading import RLock
from uuid import uuid4
from app.trading.graphs.research_graph import run_research
from app.trading.agents.historical_evidence import build_historical_evidence

_LOCK = RLock()
_RUNS: OrderedDict[str, dict] = OrderedDict()
_EXECUTOR = ThreadPoolExecutor(max_workers=1, thread_name_prefix="forex-research")
_MAX_RUNS = 30


def _now():
    return datetime.now(timezone.utc).isoformat()


def start_run(instrument: str, *, historical: bool = False) -> dict:
    if instrument not in {"EURUSD", "GBPUSD", "USDJPY"}:
        raise ValueError("Unsupported instrument")
    with _LOCK:
        if any(run["status"] in {"queued", "running"} for run in _RUNS.values()):
            raise RuntimeError("A Forex research run is already active")
        run_id = str(uuid4())
        run = {"run_id": run_id, "instrument": instrument, "status": "queued", "created_at": _now(), "updated_at": _now(), "events": [], "findings": {}, "report": None, "error": None, "decision": "NO_TRADE", "research_only": True, "evidence_mode": "historical" if historical else "none", "provenance": None}
        _RUNS[run_id] = run
        while len(_RUNS) > _MAX_RUNS:
            _RUNS.popitem(last=False)
        _EXECUTOR.submit(_execute, run_id, instrument, historical)
        return dict(run)


def _execute(run_id: str, instrument: str, historical: bool = False) -> None:
    with _LOCK:
        _RUNS[run_id].update(status="running", updated_at=_now())
    try:
        # No user-supplied 'verified' claims are accepted by this endpoint.
        # No-context graph runs fail closed and do not invoke Ollama.
        context = build_historical_evidence(instrument) if historical else None
        result = run_research(instrument, verified_context=context['verified_context'] if context else None)
        with _LOCK:
            _RUNS[run_id].update(status="completed", updated_at=_now(), events=result["events"], findings=result["findings"], report={**result["report"], "provenance": context["provenance"] if context else None}, provenance=context["provenance"] if context else None)
    except Exception as exc:
        with _LOCK:
            _RUNS[run_id].update(status="failed", updated_at=_now(), error=f"Research failed ({type(exc).__name__})")


def get_run(run_id: str) -> dict | None:
    with _LOCK:
        run = _RUNS.get(run_id)
        return dict(run) if run is not None else None


def list_runs() -> list[dict]:
    with _LOCK:
        return [dict(run) for run in reversed(_RUNS.values())]
