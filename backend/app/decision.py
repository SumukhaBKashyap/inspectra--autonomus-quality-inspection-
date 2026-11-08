"""
Inspectra – Quality Decision Engine.

Collects results from CV, Laser and Eddy modules and emits one of:
  PASS   – component meets all criteria, route by type
  FAIL   – hard defect detected, stop for manual rejection
  REVIEW – borderline or uncertain, stop for manual review
  UNKNOWN – component type could not be determined, stop for ID

Also owns the in-process WebSocket update queues.
"""

from __future__ import annotations

import asyncio
from typing import Dict, Any, Optional

from . import config


# ---------------------------------------------------------------------------
# WebSocket update queues (in-process pub/sub)
# ---------------------------------------------------------------------------
_queues: Dict[str, asyncio.Queue] = {}


def get_update_queue(inspection_id: str) -> asyncio.Queue:
    """Return (and create if needed) the update queue for an inspection."""
    if inspection_id not in _queues:
        _queues[inspection_id] = asyncio.Queue()
    return _queues[inspection_id]


async def report_progress(inspection_id: str, event_type: str, payload: Any) -> None:
    """Push a progress event onto the inspection's WebSocket queue."""
    queue = get_update_queue(inspection_id)
    await queue.put({"type": event_type, "data": payload})


def close_queue(inspection_id: str) -> None:
    """Remove the queue when the inspection is finished (WS can drain and close)."""
    _queues.pop(inspection_id, None)


# ---------------------------------------------------------------------------
# Decision logic
# ---------------------------------------------------------------------------

def evaluate(
    cv: Dict[str, Any],
    laser: Dict[str, Any],
    eddy: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Evaluate the three module results and return a decision dict:
        outcome: PASS | FAIL | REVIEW | UNKNOWN
        reasons: list[str]  – human-readable explanation for each flag
    """
    reasons: list[str] = []
    fail_flags: list[bool] = []
    review_flags: list[bool] = []

    # ---- Computer Vision ------------------------------------------------
    component_type: str = cv.get("component_type", "unknown")

    if component_type == "unknown":
        if config.DECISION_REVIEW_ON_UNKNOWN_TYPE:
            review_flags.append(True)
            reasons.append("CV: component type could not be determined → REVIEW")
        else:
            fail_flags.append(True)
            reasons.append("CV: component type could not be determined → FAIL")
    
    cv_defects: list = cv.get("defects", [])
    if cv_defects and config.DECISION_FAIL_ON_CV_DEFECTS:
        fail_flags.append(True)
        reasons.append(f"CV: {len(cv_defects)} surface defect(s) detected: {', '.join(cv_defects)}")

    # ---- Laser ----------------------------------------------------------
    laser_anomalies: list = laser.get("anomalies", [])
    if laser_anomalies and config.DECISION_FAIL_ON_LASER_ANOMALY:
        fail_flags.append(True)
        reasons.append(f"Laser: {len(laser_anomalies)} surface profile anomaly(ies): {', '.join(str(a) for a in laser_anomalies)}")

    # ---- Eddy Current (SIMULATED) ---------------------------------------
    eddy_anomalies: list = eddy.get("anomalies", [])
    if eddy_anomalies and config.DECISION_FAIL_ON_EDDY_ANOMALY:
        fail_flags.append(True)
        reasons.append(f"Eddy (SIMULATED): {len(eddy_anomalies)} anomaly(ies): {', '.join(str(a) for a in eddy_anomalies)}")

    # ---- Determine outcome ----------------------------------------------
    if any(fail_flags):
        outcome = "FAIL"
    elif any(review_flags):
        outcome = "REVIEW"
    elif component_type == "unknown":
        outcome = "UNKNOWN"
    else:
        outcome = "PASS"

    if not reasons:
        reasons.append("All inspection criteria met.")

    return {
        "outcome": outcome,
        "component_type": component_type,
        "reasons": reasons,
        "reasons_text": " | ".join(reasons),
    }
