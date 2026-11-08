"""
Inspectra – Triangular Laser Profiling Module.

Acquires a laser line profile (structured-light triangulation), calibrates
camera-laser geometry, computes a surface height map, and detects anomalies.

Camera + laser geometry parameters are configurable via environment variables.
"""

from __future__ import annotations

import os
import math
from typing import Dict, Any, List, Optional, Tuple

import cv2
import numpy as np

from . import config


# ---------------------------------------------------------------------------
# Calibration parameters (can be overridden via env vars)
# ---------------------------------------------------------------------------

# Laser line angle relative to camera plane (degrees)
LASER_ANGLE_DEG   = float(os.getenv("LASER_ANGLE_DEG",   "30.0"))
# Distance from camera to laser line plane (mm)
LASER_STAND_OFF_MM = float(os.getenv("LASER_STAND_OFF_MM", "150.0"))
# Camera pixel pitch (mm/px) in vertical direction
LASER_PX_PITCH_MM  = float(os.getenv("LASER_PX_PITCH_MM",  "0.05"))


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _extract_laser_line(gray: np.ndarray) -> np.ndarray:
    """
    Extract the sub-pixel laser line centroid per column using Gaussian fitting.

    Parameters
    ----------
    gray : grayscale image of the laser line

    Returns
    -------
    1-D array of length = image width; value = row centroid (NaN where no line)
    """
    h, w = gray.shape
    centroids = np.full(w, np.nan)

    # Threshold to isolate bright laser stripe
    _, mask = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    for col in range(w):
        col_data = gray[:, col].astype(np.float64)
        col_mask = mask[:, col]
        active = np.where(col_mask > 0)[0]
        if len(active) == 0:
            continue
        # Weighted centroid (brightness-weighted row index)
        weights = col_data[active]
        total_weight = weights.sum()
        if total_weight > 0:
            centroids[col] = float(np.sum(active * weights) / total_weight)

    return centroids


def _centroid_to_height(centroids: np.ndarray, reference: np.ndarray) -> np.ndarray:
    """
    Convert pixel centroid displacements to height values (mm) using the
    triangulation formula:
        height = Δrow × pixel_pitch / tan(laser_angle)

    Parameters
    ----------
    centroids  : measured laser line centroids (px)
    reference  : flat-surface reference centroids (px)

    Returns
    -------
    height_mm array (NaN where centroid is NaN)
    """
    tan_angle = math.tan(math.radians(LASER_ANGLE_DEG))
    if tan_angle == 0:
        return np.zeros_like(centroids)
    delta_px = centroids - reference
    height_mm = delta_px * LASER_PX_PITCH_MM / tan_angle
    return height_mm


def _build_reference_line(width: int) -> np.ndarray:
    """
    Flat reference: assume laser line sits at the vertical midpoint
    of the frame on a perfect flat surface.
    """
    return np.full(width, 100.0)   # row 100 as a typical mid-frame reference


def _detect_anomalies(height_mm: np.ndarray) -> Tuple[List[str], Dict[str, float]]:
    """
    Flag anomalies based on:
      1. Peak-to-valley range > LASER_MAX_HEIGHT_VARIATION_MM
      2. Fraction of points deviating > 2σ from mean > LASER_ANOMALY_FRACTION_THRESHOLD

    Returns (anomaly_list, stats_dict).
    """
    valid = height_mm[~np.isnan(height_mm)]
    if len(valid) == 0:
        return ["no_valid_laser_data"], {}

    pv_range = float(np.ptp(valid))
    mean_h   = float(np.mean(valid))
    std_h    = float(np.std(valid))

    outlier_mask = np.abs(valid - mean_h) > 2 * std_h
    outlier_frac = float(np.sum(outlier_mask)) / len(valid)

    stats = {
        "peak_to_valley_mm":    round(pv_range, 4),
        "mean_height_mm":       round(mean_h,   4),
        "std_height_mm":        round(std_h,    4),
        "outlier_fraction":     round(outlier_frac, 4),
        "num_valid_points":     int(len(valid)),
    }

    anomalies: List[str] = []
    if pv_range > config.LASER_MAX_HEIGHT_VARIATION_MM:
        anomalies.append(
            f"height_variation {pv_range:.3f}mm exceeds max "
            f"{config.LASER_MAX_HEIGHT_VARIATION_MM}mm"
        )
    if outlier_frac > config.LASER_ANOMALY_FRACTION_THRESHOLD:
        anomalies.append(
            f"outlier_fraction {outlier_frac:.3f} exceeds threshold "
            f"{config.LASER_ANOMALY_FRACTION_THRESHOLD}"
        )

    return anomalies, stats


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def process_profile(
    inspection_id: str,
    laser_image_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Process a triangular laser profile image for the given inspection.

    Parameters
    ----------
    inspection_id    : unique inspection identifier (used for logging/saving)
    laser_image_path : path to laser stripe image; if None or file missing,
                       falls back to synthetic test pattern.

    Returns
    -------
    dict with keys:
        height_map  : {cols, values, stats}
        anomalies   : list[str]
        stats       : statistical summary
        source      : 'real' | 'synthetic_fallback'
    """
    source = "real"

    # --- Load or synthesise laser image ---
    img = None
    if laser_image_path and os.path.isfile(laser_image_path):
        raw = cv2.imread(laser_image_path)
        if raw is not None:
            img = cv2.cvtColor(raw, cv2.COLOR_BGR2GRAY)

    if img is None:
        # Synthetic fallback: flat surface + small Gaussian bump to simulate a component
        source = "synthetic_fallback"
        width, height = 320, 240
        img = np.zeros((height, width), dtype=np.uint8)
        # Laser line at row 100, slightly curved over component area
        for col in range(width):
            # Gaussian bump centered at mid-width, height 15 px
            row = int(100 - 15 * math.exp(-((col - width / 2) ** 2) / (2 * (width / 6) ** 2)))
            if 0 <= row < height:
                # Draw 3-pixel wide stripe
                for dr in range(-1, 2):
                    r = row + dr
                    if 0 <= r < height:
                        img[r, col] = max(0, min(255, 200 - abs(dr) * 60))

    # --- Extract laser line centroids ---
    centroids = _extract_laser_line(img)
    reference = _build_reference_line(img.shape[1])

    # --- Convert to height map ---
    height_mm = _centroid_to_height(centroids, reference)

    # --- Detect anomalies ---
    anomalies, stats = _detect_anomalies(height_mm)

    # Serialise height map (replace NaN with None for JSON)
    height_values = [None if math.isnan(v) else round(float(v), 4) for v in height_mm]

    return {
        "height_map": {
            "cols":   len(height_values),
            "values": height_values,
        },
        "anomalies": anomalies,
        "stats":     stats,
        "source":    source,
    }
