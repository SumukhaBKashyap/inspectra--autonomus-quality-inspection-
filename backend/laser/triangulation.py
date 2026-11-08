"""
Inspectra - Laser Triangulation and Height Variation Analysis
Converts sub-pixel laser line shifts to calibrated surface height measurements:
    height = Δrow * pixel_pitch / tan(laser_angle)
Compares profile against reference limits and flags surface irregularities.
Clearly distinguishes calibrated measurements from uncalibrated approximations.
"""

import math
from typing import Dict, Any, List
import numpy as np
from ..config import config

def compute_triangulation_height(
    centroids: np.ndarray,
    baseline: np.ndarray,
    metal_type: Optional[str] = None,
    analysis_mode: Optional[str] = None
) -> Dict[str, Any]:
    """
    Compute surface height profile in millimetres and detect surface anomalies
    w.r.t the active metal and analysis criteria.
    """
    is_calibrated = config.LASER_CALIBRATED
    laser_angle_deg = config.LASER_ANGLE_DEG
    pixel_pitch_mm = config.LASER_PX_PITCH_MM
    
    metal = config.get_metal_profile(metal_type)
    mode = config.get_analysis_mode(analysis_mode)
    
    base_tol = float(metal.get("laser_roughness_mm", config.LASER_MAX_HEIGHT_VARIATION_MM))
    max_height_tol = round(base_tol * float(mode["laser_tolerance_multiplier"]), 2)

    tan_angle = math.tan(math.radians(laser_angle_deg))
    if tan_angle == 0:
        tan_angle = 0.001

    # Vertical displacement (pixels shifted up on camera sensor = positive height)
    # Note: image row 0 is top, so baseline - centroid gives positive displacement
    delta_pixels = baseline - centroids

    if is_calibrated:
        height_mm = delta_pixels * (pixel_pitch_mm / tan_angle)
    else:
        # Uncalibrated: use pixel displacement directly as arbitrary estimate units
        height_mm = delta_pixels * 0.1

    # Filter out NaNs where no laser line was seen
    valid_mask = ~np.isnan(height_mm)
    valid_heights = height_mm[valid_mask]

    anomalies: List[str] = []

    if len(valid_heights) < 20:
        return {
            "status": "FAIL",
            "is_calibrated": is_calibrated,
            "error": "Insufficient laser profile data across component surface",
            "max_height_variation_mm": 0.0,
            "mean_height_mm": 0.0,
            "peak_height_mm": 0.0,
            "profile_sample": [],
            "anomalies": ["Laser line was occluded or insufficient contrast"]
        }

    # Restrict to active component region (where height > 0.5 mm)
    comp_mask = valid_heights > 0.5
    comp_heights = valid_heights[comp_mask]

    if len(comp_heights) == 0:
        comp_heights = valid_heights

    mean_h = float(np.mean(comp_heights))
    peak_h = float(np.max(comp_heights))

    # Evaluate the top surface plateau of the component for flatness, warpage and burrs
    # Fastener thickness (2mm-8mm) is normal physical geometry; tolerance applies to top plateau flatness
    flatness_limit_mm = max(3.2, max_height_tol * 3.5)
    plateau_mask = comp_heights >= (peak_h * 0.70)
    
    if np.sum(plateau_mask) >= 8:
        plateau = comp_heights[plateau_mask]
        peak_to_valley = float(np.max(plateau) - np.min(plateau))
        std_h = float(np.std(plateau))
    else:
        min_h = float(np.min(comp_heights))
        peak_to_valley = float(peak_h - min_h)
        std_h = float(np.std(comp_heights))

    # Anomaly checks: Only flag if plateau has extreme warpage or severe mechanical burrs
    if peak_to_valley > flatness_limit_mm:
        anomalies.append(
            f"Laser: top plateau height variation {peak_to_valley:.2f} mm exceeds tolerance {flatness_limit_mm:.2f} mm (severe warpage)"
        )
    if std_h > (flatness_limit_mm * 0.65):
        anomalies.append(
            f"Laser: surface profile roughness (std {std_h:.2f} mm) indicates irregular surface curvature"
        )

    # Sample profile down to 60 points for JSON serialization & frontend charting
    step = max(1, len(height_mm) // 60)
    sampled_profile = []
    for i in range(0, len(height_mm), step):
        val = height_mm[i]
        sampled_profile.append({
            "x": i,
            "height": round(float(val), 2) if not np.isnan(val) else 0.0,
            "ref_baseline": 0.0
        })

    status = "FAIL" if len(anomalies) > 0 else "PASS"

    return {
        "status": status,
        "is_calibrated": is_calibrated,
        "max_height_variation_mm": round(peak_to_valley, 2),
        "mean_height_mm": round(mean_h, 2),
        "peak_height_mm": round(peak_h, 2),
        "roughness_std_mm": round(std_h, 3),
        "profile_sample": sampled_profile,
        "anomalies": anomalies,
        "calibration_notice": "CALIBRATED GEOMETRY" if is_calibrated else "UNCALIBRATED ESTIMATE"
    }
