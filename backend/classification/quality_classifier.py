"""
Inspectra - Quality Classifier
Evaluates CV, Laser, and Eddy-Current module metrics individually.
"""

from typing import Dict, Any, List
from ..config import config

def evaluate_cv_quality(cv_result: Dict[str, Any]) -> Dict[str, Any]:
    comp_type = cv_result.get("component_type", "unknown")
    status = cv_result.get("status", "FAIL")
    stream_pass_pct = float(cv_result.get("stream_pass_pct", 100.0 if status == "PASS" else 0.0))
    defects = cv_result.get("defects", [])
    
    reasons: List[str] = []
    
    if comp_type == "unknown":
        reasons.append("Component geometry not recognized as nut or washer")
        return {"status": "REVIEW" if config.DECISION_REVIEW_ON_UNKNOWN_TYPE else "FAIL", "reasons": reasons}

    # Pass the component if stream passing percentage is > 50% or status is PASS
    if stream_pass_pct > 50.0 or status == "PASS":
        return {"status": "PASS", "reasons": [f"Stream pass rate ({stream_pass_pct}%) exceeds 50% threshold"]}

    if defects and config.DECISION_FAIL_ON_CV_DEFECTS:
        reasons.extend(defects)
        return {"status": "FAIL", "reasons": reasons}

    return {"status": "PASS", "reasons": ["Surface integrity, perimeter edge, and finish meet quality standards"]}

    if defects and config.DECISION_FAIL_ON_CV_DEFECTS:
        reasons.extend(defects)
        return {"status": "FAIL", "reasons": reasons}

    if not within_tol:
        reasons.append("Measured dimensions exceed reference tolerances")
        return {"status": "FAIL", "reasons": reasons}

    return {"status": "PASS", "reasons": ["Visual geometry and surface meet specifications"]}

def evaluate_laser_quality(laser_result: Dict[str, Any]) -> Dict[str, Any]:
    anomalies = laser_result.get("anomalies", [])
    if anomalies and config.DECISION_FAIL_ON_LASER_ANOMALY:
        return {"status": "FAIL", "reasons": anomalies}
    return {"status": "PASS", "reasons": ["Laser height profile within tolerance envelope"]}

def evaluate_eddy_quality(eddy_result: Dict[str, Any]) -> Dict[str, Any]:
    anomalies = eddy_result.get("anomalies", [])
    if anomalies and config.DECISION_FAIL_ON_EDDY_ANOMALY:
        return {"status": "FAIL", "reasons": anomalies}
    return {"status": "PASS", "reasons": ["Coil impedance deviations within baseline"]}

