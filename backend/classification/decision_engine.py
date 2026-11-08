"""
Inspectra - Central Intelligent Decision Engine
Fuses independent inspection results from:
  1. Multi-Angle Computer Vision (REAL)
  2. Triangular Laser Profiling (REAL)
  3. Eddy Current Array

Decides overall status: PASS, FAIL, or REVIEW.
Determines sorting action:
  - PASS + NUT    -> SORT_NUT (Servo 3 diverts to nut bin)
  - PASS + WASHER -> SORT_WASHER (Servo 3 diverts to washer bin)
  - FAIL          -> STOP_CONVEYOR (Halt for manual removal)
  - REVIEW        -> STOP_CONVEYOR (Halt for manual inspection)
  - UNKNOWN       -> STOP_CONVEYOR (Halt for manual identification)
"""

from typing import Dict, Any, List, Optional
from ..config import config
from .quality_classifier import evaluate_cv_quality, evaluate_laser_quality, evaluate_eddy_quality

def make_quality_decision(
    cv_data: Optional[Dict[str, Any]],
    laser_data: Optional[Dict[str, Any]],
    eddy_data: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Main decision engine function.
    """
    reasons: List[str] = []

    # Rule: Do not automatically classify a component as PASS when required inspection data is unavailable
    if cv_data is None or laser_data is None or eddy_data is None:
        missing = []
        if cv_data is None: missing.append("CV")
        if laser_data is None: missing.append("Laser")
        if eddy_data is None: missing.append("Eddy")
        return {
            "component_type": "UNKNOWN",
            "cv_status": "REVIEW",
            "laser_status": "REVIEW",
            "eddy_status": "REVIEW",
            "quality_status": "REVIEW",
            "final_reason": f"Required inspection data unavailable: {', '.join(missing)} → Manual Review Required",
            "sorting_command": "STOP_CONVEYOR"
        }

    # Extract component type from CV
    raw_type = str(cv_data.get("component_type", "unknown")).upper()
    if raw_type not in ["NUT", "WASHER"]:
        comp_type = "UNKNOWN"
    else:
        comp_type = raw_type

    # Evaluate each module independently
    cv_eval = evaluate_cv_quality(cv_data)
    laser_eval = evaluate_laser_quality(laser_data)
    eddy_eval = evaluate_eddy_quality(eddy_data)

    cv_status = cv_eval["status"]
    laser_status = laser_eval["status"]
    eddy_status = eddy_eval["status"]

    # Multi-method consensus: Pass if stream passing percentage is > 50% (at least 2 of 3 modules pass)
    methods_passed = sum(1 for s in [cv_status, laser_status, eddy_status] if s == "PASS")
    methods_pass_pct = (methods_passed / 3.0) * 100.0

    # Determine Quality Status
    if comp_type == "UNKNOWN":
        quality_status = "REVIEW"
        reasons.append("Uncertain component geometry: not identifiable as nut or washer")
    elif methods_passed >= 2 and cv_status == "PASS":
        quality_status = "PASS"
        reasons.append(f"Inspection passing rate ({methods_pass_pct:.0f}%) exceeds 50% threshold for {comp_type}")
    elif (cv_status == "FAIL") or (laser_status == "FAIL") or (eddy_status == "FAIL"):
        quality_status = "FAIL"
        if cv_status == "FAIL":
            reasons.extend([f"CV: {r}" for r in cv_eval["reasons"]])
        if laser_status == "FAIL":
            reasons.extend([f"Laser: {r}" for r in laser_eval["reasons"]])
        if eddy_status == "FAIL":
            reasons.extend([f"Eddy Current: {r}" for r in eddy_eval["reasons"]])
    elif (cv_status == "REVIEW") or (laser_status == "REVIEW") or (eddy_status == "REVIEW"):
        quality_status = "REVIEW"
        if cv_status == "REVIEW":
            reasons.extend([f"CV: {r}" for r in cv_eval["reasons"]])
        if laser_status == "REVIEW":
            reasons.extend([f"Laser: {r}" for r in laser_eval["reasons"]])
        if eddy_status == "REVIEW":
            reasons.extend([f"Eddy Current: {r}" for r in eddy_eval["reasons"]])
    else:
        quality_status = "PASS"
        reasons.append(f"All 3 quality inspection methods PASSED for {comp_type}")

    # Determine Sorting Command
    # FAIL, REVIEW and UNKNOWN components must stop the conveyor for manual handling.
    if quality_status == "PASS" and comp_type == "NUT":
        sorting_command = "SORT_NUT"
    elif quality_status == "PASS" and comp_type == "WASHER":
        sorting_command = "SORT_WASHER"
    else:
        sorting_command = "STOP_CONVEYOR"

    final_reason_text = " | ".join(reasons) if reasons else "Inspection completed"

    return {
        "component_type": comp_type,
        "cv_status": cv_status,
        "laser_status": laser_status,
        "eddy_status": eddy_status,
        "quality_status": quality_status,
        "final_reason": final_reason_text,
        "sorting_command": sorting_command,
        "cv_details": cv_eval,
        "laser_details": laser_eval,
        "eddy_details": eddy_eval
    }

