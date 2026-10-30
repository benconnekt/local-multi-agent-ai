"""Read-only robustness diagnostics on previously exported hypothetical trade ledgers.

This is NOT a genuine unseen-data walk-forward test: strategy and cohort are already known.
No broker integration, data certification, or trade eligibility.
"""
from __future__ import annotations

from datetime import datetime, timezone
from math import isfinite
from typing import Any

SAFE = {"decision": "NO_TRADE", "research_only": True,
        "quality_certified": False, "research_signal_eligible": False,
        "independently_certified": False, "hypothetical": True}


def _timestamp(value: str) -> datetime:
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        raise ValueError("Naive trade timestamp")
    return dt.astimezone(timezone.utc)


def _metrics(trades: list[dict[str, Any]]) -> dict[str, Any]:
    realised = [float(t["r_multiple"]) for t in trades if t["outcome"] in ("win", "loss")]
    wins = sum(t["outcome"] == "win" for t in trades)
    losses = sum(t["outcome"] == "loss" for t in trades)
    equity = peak = dd = 0.0
    for r in realised:
        equity += r
        peak = max(peak, equity)
        dd = max(dd, peak - equity)
    return {"trades": len(trades), "resolved": len(realised), "wins": wins,
            "losses": losses, "unresolved": len(trades) - len(realised),
            "total_r": sum(realised),
            "expectancy_r": sum(realised) / len(realised) if realised else None,
            "win_rate": wins / len(realised) if realised else None,
            "max_drawdown_r": dd}


def analyse_ledger(export: dict[str, Any], *, holdout_fraction: float = .30,
                   minimum_holdout_resolved: int = 30) -> dict[str, Any]:
    """Chronological diagnostic split; never call the holdout genuinely unseen."""
    if not (0 < holdout_fraction < 1):
        raise ValueError("holdout_fraction must be between zero and one")
    if minimum_holdout_resolved < 1:
        raise ValueError("minimum_holdout_resolved must be positive")
    if any(export.get(k) != v for k, v in SAFE.items() if k in export):
        raise ValueError("Unsafe input ledger flags")
    if export.get("decision") != "NO_TRADE" or export.get("audit_pass") is not True:
        raise ValueError("Only audited, research-only NO_TRADE ledgers accepted")
    ledger = export.get("ledger")
    if not isinstance(ledger, list):
        raise ValueError("Missing ledger")
    seen = set()
    ordered = sorted(ledger, key=lambda t: _timestamp(t["signal_time_utc"]))
    for trade in ordered:
        stamp = _timestamp(trade["signal_time_utc"])
        if stamp in seen:
            raise ValueError("Duplicate signal timestamp")
        seen.add(stamp)
        if trade["direction"] not in ("LONG", "SHORT"):
            raise ValueError("Invalid trade direction")
        if trade["outcome"] not in ("win", "loss", "unresolved"):
            raise ValueError("Invalid outcome")
        r = trade.get("r_multiple")
        if trade["outcome"] == "unresolved":
            if r is not None:
                raise ValueError("Unresolved trade has realised R")
        elif not isinstance(r, (int, float)) or not isfinite(r):
            raise ValueError("Invalid realised R")
    cut = int(len(ordered) * (1 - holdout_fraction))
    train, holdout = ordered[:cut], ordered[cut:]
    holdout_metrics = _metrics(holdout)
    return {**SAFE, "instrument": export.get("instrument"),
            "validation_type": "retrospective_chronological_diagnostic_not_out_of_sample",
            "strategy_frozen_before_holdout": False,
            "historical_data_independently_certified": False,
            "split": {"training": _metrics(train), "holdout": holdout_metrics,
                      "boundary_signal_utc": holdout[0]["signal_time_utc"] if holdout else None},
            "by_direction": {side: _metrics([t for t in ordered if t["direction"] == side])
                             for side in ("LONG", "SHORT")},
            "by_weekend_hold": {"held": _metrics([t for t in ordered if t.get("weekend_hold") is True]),
                                "not_held": _metrics([t for t in ordered if t.get("weekend_hold") is False])},
            "sample_sufficient": holdout_metrics["resolved"] >= minimum_holdout_resolved,
            "validation_pass": False,
            "blockers": ["Existing ledger is not genuinely unseen data",
                         "Independent market-data/session certification pending",
                         *([f"Holdout has fewer than {minimum_holdout_resolved} resolved trades"]
                           if holdout_metrics["resolved"] < minimum_holdout_resolved else [])],
            "limitations": ["Fixed-cohort cost sensitivity requires original OHLC and re-simulation",
                            "No financing, bid/ask path, or variable liquidity modelling",
                            "A diagnostic split cannot prove strategy generalisation"]}
