"""
Inspectra - Settings API Endpoints
Provides reading and updating of inspection thresholds, calibration values,
camera options, serial ports, and simulation mode.
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter
from pydantic import BaseModel
from ..config import config, DEFAULT_CONFIG, METAL_PROFILES, ANALYSIS_MODES

router = APIRouter(prefix="/api/settings", tags=["settings"])

class MaterialSelectionRequest(BaseModel):
    metal_type: Optional[str] = None
    analysis_mode: Optional[str] = None

@router.get("/metal-profiles")
def get_metal_profiles():
    """Return available metals, analysis modes, and the currently active profile."""
    return {
        "metals": METAL_PROFILES,
        "modes": ANALYSIS_MODES,
        "selected_metal": config.SELECTED_METAL,
        "analysis_type": config.ANALYSIS_TYPE
    }

@router.post("/material-selection")
def update_material_selection(req: MaterialSelectionRequest):
    """Update active metal profile and analysis mode."""
    updates = {}
    if req.metal_type and req.metal_type in METAL_PROFILES:
        updates["SELECTED_METAL"] = req.metal_type
    if req.analysis_mode and req.analysis_mode in ANALYSIS_MODES:
        updates["ANALYSIS_TYPE"] = req.analysis_mode
    if updates:
        config.update(updates)
    return {
        "status": "updated",
        "selected_metal": config.SELECTED_METAL,
        "analysis_type": config.ANALYSIS_TYPE,
        "active_profile": METAL_PROFILES.get(config.SELECTED_METAL),
        "active_mode_info": ANALYSIS_MODES.get(config.ANALYSIS_TYPE)
    }

class TargetDimensionsRequest(BaseModel):
    required_outer_mm: float
    required_inner_mm: float
    required_tolerance_mm: Optional[float] = 0.45
    preset: Optional[str] = "CUSTOM"

@router.get("/target-dimensions")
def get_target_dimensions():
    """Return currently calibrated required dimensions for Pass/Fail decision."""
    return {
        "required_outer_mm": config.REQUIRED_OUTER_MM,
        "required_inner_mm": config.REQUIRED_INNER_MM,
        "required_tolerance_mm": config.REQUIRED_TOLERANCE_MM,
        "preset": getattr(config, "CALIBRATION_PRESET", "M5")
    }

@router.post("/target-dimensions")
def update_target_dimensions(req: TargetDimensionsRequest):
    """Calibrate required dimensions to determine Pass or Fail in AI inspections."""
    updates = {
        "REQUIRED_OUTER_MM": round(req.required_outer_mm, 2),
        "REQUIRED_INNER_MM": round(req.required_inner_mm, 2),
        "REQUIRED_TOLERANCE_MM": round(req.required_tolerance_mm or 0.45, 2),
        "CALIBRATION_PRESET": req.preset or "CUSTOM"
    }
    config.update(updates)
    return {
        "status": "calibrated",
        "required_outer_mm": config.REQUIRED_OUTER_MM,
        "required_inner_mm": config.REQUIRED_INNER_MM,
        "required_tolerance_mm": config.REQUIRED_TOLERANCE_MM,
        "preset": config.CALIBRATION_PRESET
    }

@router.get("")
def get_settings():
    """Return all active configuration parameters."""
    return config.all()

@router.post("")
def update_settings(updates: Dict[str, Any]):
    """Update settings and persist to settings.json."""
    config.update(updates)
    return {"status": "saved", "config": config.all()}

@router.post("/reset")
def reset_settings():
    """Reset configuration back to default factory parameters."""
    config.update(DEFAULT_CONFIG)
    return {"status": "reset_to_default", "config": config.all()}

