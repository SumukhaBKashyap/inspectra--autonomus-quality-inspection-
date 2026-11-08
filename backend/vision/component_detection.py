"""
Inspectra - High-Precision Component Identification Module (Nut vs Washer & M3-M8 Sizing)
Combines:
- Trained Random Forest ML model on 1,500 industrial images with 45° perspective correction
- Multi-scale polygon vertex detection (approxPolyDP) with angular spacing verification
- Sub-pixel corner refinement (cornerSubPix)
- Geometric radial harmonic variance & circularity
- Precision inner hole detection
"""

import os
import math
import logging
from typing import Optional, Dict, Any, Tuple, List
import cv2
import numpy as np
import joblib

logger = logging.getLogger("inspectra.cv")

# Global ML model bundle cache
_MODEL_BUNDLE = None

def _load_model_bundle():
    global _MODEL_BUNDLE
    if _MODEL_BUNDLE is not None:
        return _MODEL_BUNDLE

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    model_path = os.path.join(base_dir, "models", "component_size_bundle.pkl")
    if os.path.exists(model_path):
        try:
            _MODEL_BUNDLE = joblib.load(model_path)
            logger.info(f"[CV Model] Loaded trained M3-M8 model bundle from {model_path}")
        except Exception as e:
            logger.warning(f"[CV Model] Failed to load model bundle: {e}")
    return _MODEL_BUNDLE

def calculate_circularity(contour: np.ndarray) -> float:
    """Circularity = 4 * pi * Area / Perimeter^2. Circle = 1.0; Hexagon ≈ 0.88 - 0.91."""
    area = cv2.contourArea(contour)
    perimeter = cv2.arcLength(contour, True)
    if perimeter == 0:
        return 0.0
    return float((4.0 * math.pi * area) / (perimeter ** 2))

def find_primary_contour(binary: np.ndarray) -> Optional[np.ndarray]:
    """Find the largest contour exceeding the minimum area threshold."""
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None
    contours = sorted(contours, key=cv2.contourArea, reverse=True)
    largest = contours[0]
    if cv2.contourArea(largest) >= 300:
        return largest
    return None

def detect_inner_hole_precise(
    gray: np.ndarray,
    outer_contour: np.ndarray
) -> Tuple[bool, Optional[Tuple[float, float, float]], float]:
    """
    Precision inner hole detector using contour hierarchy and Hough circle cross-verification.
    Returns:
        has_hole: bool
        hole_circle: (center_x, center_y, radius) in sub-pixel coordinates
        eccentricity_px: Euclidean distance from outer centroid to hole center
    """
    m = cv2.moments(outer_contour)
    if m["m00"] == 0:
        outer_cx, outer_cy = 320.0, 240.0
    else:
        outer_cx = m["m10"] / m["m00"]
        outer_cy = m["m01"] / m["m00"]

    mask = np.zeros(gray.shape, dtype=np.uint8)
    cv2.drawContours(mask, [outer_contour], -1, 255, -1)
    
    inv_roi = cv2.bitwise_not(gray)
    inv_roi = cv2.bitwise_and(inv_roi, inv_roi, mask=mask)

    _, hole_bin = cv2.threshold(inv_roi, 190, 255, cv2.THRESH_BINARY)
    hole_contours, _ = cv2.findContours(hole_bin, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    for c in hole_contours:
        area = cv2.contourArea(c)
        if 80 < area < (cv2.contourArea(outer_contour) * 0.48):
            if len(c) >= 5:
                (hx, hy), (d1, d2), _ = cv2.fitEllipse(c)
                hole_r = (d1 + d2) / 4.0
                eccentricity = math.hypot(hx - outer_cx, hy - outer_cy)
                return True, (float(hx), float(hy), float(hole_r)), float(eccentricity)

    # Fallback Hough Circles
    circles = cv2.HoughCircles(
        gray,
        cv2.HOUGH_GRADIENT,
        dp=1.2,
        minDist=25,
        param1=50,
        param2=20,
        minRadius=8,
        maxRadius=85
    )
    if circles is not None and len(circles[0]) > 0:
        for c in circles[0]:
            hx, hy, hr = float(c[0]), float(c[1]), float(c[2])
            ecc = math.hypot(hx - outer_cx, hy - outer_cy)
            if ecc < (hr * 1.1):
                return True, (hx, hy, hr), float(ecc)

    return False, None, 0.0

def detect_hex_corners(
    contour: np.ndarray,
    gray: np.ndarray
) -> Tuple[int, List[Tuple[float, float]], bool]:
    """Multi-scale polygon approximation and sub-pixel corner refinement."""
    perimeter = cv2.arcLength(contour, True)
    if perimeter == 0:
        return 0, [], False

    best_corners = []
    for eps_factor in [0.030, 0.035, 0.040, 0.045]:
        approx = cv2.approxPolyDP(contour, eps_factor * perimeter, True)
        if len(approx) == 6:
            best_corners = approx
            break
        elif len(best_corners) == 0:
            best_corners = approx

    corner_pts = np.array([pt[0] for pt in best_corners], dtype=np.float32)
    is_regular_hex = False

    if len(corner_pts) == 6:
        m = cv2.moments(contour)
        cx = m["m10"] / m["m00"] if m["m00"] > 0 else 320.0
        cy = m["m01"] / m["m00"] if m["m00"] > 0 else 240.0
        angles = sorted([math.atan2(p[1] - cy, p[0] - cx) for p in corner_pts])
        diffs = [(angles[(i + 1) % 6] - angles[i]) % (2 * math.pi) for i in range(6)]
        is_regular_hex = all(abs(d - (math.pi / 3.0)) < 0.38 for d in diffs)

        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.01)
        try:
            corner_pts = cv2.cornerSubPix(gray, corner_pts, (5, 5), (-1, -1), criteria)
        except Exception:
            pass

    return len(corner_pts), [(float(p[0]), float(p[1])) for p in corner_pts], is_regular_hex

def classify_component(contour: np.ndarray, gray: np.ndarray, tilt_deg: float = 45.0) -> Dict[str, Any]:
    """
    Classify component into NUT or WASHER and predict its metric size (M3 to M8)
    using the trained Random Forest model bundle + geometric verification.
    """
    circ = calculate_circularity(contour)
    num_corners, corners_pts, is_regular_hex = detect_hex_corners(contour, gray)
    has_hole, hole_circle, hole_eccentricity_px = detect_inner_hole_precise(gray, contour)

    # 1. Perspective Rectification along 45° tilt axis (Y scale = 1 / cos(45°) ≈ 1.4142)
    cos_tilt = math.cos(math.radians(tilt_deg))
    scale_y = 1.0 / cos_tilt if cos_tilt > 0.1 else 1.4142

    m = cv2.moments(contour)
    cx = m["m10"] / m["m00"] if m["m00"] > 0 else 320.0
    cy = m["m01"] / m["m00"] if m["m00"] > 0 else 240.0

    pts_rect = []
    for pt in contour:
        px, py = pt[0]
        ry = (py - cy) * scale_y + cy
        pts_rect.append([[px, ry]])
    c_rect = np.int32(np.array(pts_rect, dtype=np.float32))

    area_rect = cv2.contourArea(c_rect)
    perim_rect = cv2.arcLength(c_rect, True)
    circ_rect = (4.0 * math.pi * area_rect) / (perim_rect ** 2) if perim_rect > 0 else 0.0

    if len(c_rect) >= 5:
        _, (ax1, ax2), _ = cv2.fitEllipse(c_rect)
        major_px = max(ax1, ax2)
        minor_px = max(1.0, min(ax1, ax2))
    else:
        _, r = cv2.minEnclosingCircle(c_rect)
        major_px = r * 2.0
        minor_px = r * 2.0

    aspect_ratio = major_px / minor_px
    best_corners = cv2.approxPolyDP(c_rect, 0.035 * perim_rect, True)
    rect_corner_count = len(best_corners)

    # Hex angular variance
    hex_ang_var = 1.0
    if rect_corner_count == 6:
        c_pts = [p[0] for p in best_corners]
        angles = sorted([math.atan2(p[1] - cy, p[0] - cx) for p in c_pts])
        diffs = [(angles[(i + 1) % 6] - angles[i]) % (2 * math.pi) for i in range(6)]
        hex_ang_var = float(np.mean([abs(d - (math.pi / 3.0)) for d in diffs]))

    radii = [math.hypot(p[0][0] - cx, p[0][1] - cy) for p in c_rect]
    rad_mean = np.mean(radii) if radii else 1.0
    rad_std = np.std(radii) if radii else 0.0
    rad_var_ratio = rad_std / rad_mean if rad_mean > 0 else 0.0

    hole_major_px = hole_circle[2] * 2.0 if hole_circle else 0.0
    inner_outer_ratio = hole_major_px / major_px if major_px > 0 else 0.0

    feat_vector = np.array([[
        major_px,
        minor_px,
        aspect_ratio,
        area_rect,
        perim_rect,
        circ_rect,
        rect_corner_count,
        hex_ang_var,
        rad_var_ratio,
        1.0 if has_hole else 0.0,
        hole_major_px,
        inner_outer_ratio,
        hole_eccentricity_px
    ]], dtype=np.float32)

    # 2. Query ML Model Bundle
    bundle = _load_model_bundle()
    comp_type = "unknown"
    metric_size = "UNKNOWN"
    confidence = 0.50

    if bundle is not None:
        try:
            pred_type = bundle["clf_type"].predict(feat_vector)[0]
            probs_type = bundle["clf_type"].predict_proba(feat_vector)[0]
            comp_type = "washer" if pred_type == 1 else "nut"
            conf_type = float(probs_type[pred_type])

            pred_size_idx = bundle["clf_size"].predict(feat_vector)[0]
            metric_size = bundle["inv_size_map"].get(pred_size_idx, "M5")
            confidence = round(conf_type, 3)
        except Exception as e:
            logger.debug(f"[CV Model] Prediction fallback: {e}")

    # Geometric rule sanity check / fallback
    if comp_type == "unknown":
        if is_regular_hex and (circ <= 0.93):
            comp_type = "nut"
            confidence = 0.95
        elif circ >= 0.88 or has_hole:
            comp_type = "washer"
            confidence = min(0.98, max(0.80, circ))
        elif is_regular_hex:
            comp_type = "nut"
            confidence = 0.82
        else:
            comp_type = "unknown"
            confidence = 0.35

    # Fallback metric size by major diameter if unknown
    if metric_size == "UNKNOWN":
        outer_mm = major_px * 0.12
        if outer_mm < 7.5:
            metric_size = "M3"
        elif outer_mm < 9.5:
            metric_size = "M4"
        elif outer_mm < 11.2:
            metric_size = "M5"
        elif outer_mm < 14.0:
            metric_size = "M6"
        else:
            metric_size = "M8"

    return {
        "component_type": comp_type,
        "metric_size": metric_size,
        "confidence": confidence,
        "circularity": round(circ, 3),
        "rectified_circularity": round(circ_rect, 3),
        "radial_harmonic_variance": round(rad_var_ratio, 3),
        "corners": num_corners,
        "corner_points": corners_pts,
        "is_regular_hex": is_regular_hex,
        "has_hole": has_hole,
        "hole_circle": hole_circle,
        "hole_eccentricity_px": round(hole_eccentricity_px, 2)
    }
