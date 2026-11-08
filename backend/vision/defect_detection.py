"""
Inspectra - High-Precision Visible Surface Defect Detection Module
Analyzes visible surface anomalies:
1. Perimeter defects: burrs, notches, chips, and deformations via convex hull analysis
2. Face defects: scratches, cracks, and pit marks via high-pass gradient and dark patch filters
3. Material finish: corrosion, oxidation stains, and discoloration patches
"""

from typing import List, Dict, Any, Tuple, Optional
import cv2
import numpy as np
from ..config import config

def detect_surface_defects_precise(
    contour: np.ndarray,
    gray: np.ndarray,
    binary: np.ndarray,
    hole_circle: Optional[Tuple[float, float, float]] = None,
    metal_type: Optional[str] = None,
    analysis_mode: Optional[str] = None,
    color_img: Optional[np.ndarray] = None
) -> Dict[str, Any]:
    """
    Precision surface, perimeter, and alloy defect inspection w.r.t metal criteria.
    """
    defects: List[str] = []
    metal = config.get_metal_profile(metal_type)
    mode = config.get_analysis_mode(analysis_mode)
    tol_mult = float(mode.get("tolerance_multiplier", 1.0))
    max_defect_frac = float(mode.get("cv_defect_area_limit", config.CV_MAX_DEFECT_FRACTION)) * tol_mult

    # Mode-adaptive threshold limits based on selected standard (Standard vs Aerospace vs High-Speed)
    notch_limit_px = 12.0 * tol_mult
    variance_limit = 54.0 * tol_mult
    lap_thresh = int(65 / max(0.5, tol_mult))
    min_scratch_px = int(35 * tol_mult)

    # ---------------- 1. Perimeter Edge Defect Analysis ----------------
    (cx, cy), enc_r = cv2.minEnclosingCircle(contour)
    rads = np.hypot(contour[:, 0, 0] - cx, contour[:, 0, 1] - cy)
    radial_dev = float(np.max(rads) - np.median(rads))

    hull = cv2.convexHull(contour, returnPoints=False)
    if len(hull) > 3:
        try:
            convexity_defects = cv2.convexityDefects(contour, hull)
            if convexity_defects is not None:
                deep_notches = 0
                max_depth_px = 0.0
                for i in range(convexity_defects.shape[0]):
                    s, e, f, d = convexity_defects[i, 0]
                    depth_px = d / 256.0
                    if depth_px > max_depth_px:
                        max_depth_px = depth_px
                    # Notches exceeding tolerance indicate perimeter damage / burrs
                    if depth_px > notch_limit_px:
                        deep_notches += 1

                if deep_notches >= 2:
                    defects.append(f"[Perimeter] Edge notch/burr detected: {deep_notches} anomalies (max depth {max_depth_px:.1f} px)")
        except Exception:
            pass

    # Radial protrusion check for circular components (washers)
    circ = (4.0 * np.pi * cv2.contourArea(contour)) / (cv2.arcLength(contour, True) ** 2)
    if circ >= 0.88 and radial_dev > (14.0 * tol_mult) and len(defects) == 0:
        defects.append(f"[Perimeter] Burr detected: radial protrusion {radial_dev:.1f} px exceeds limit")

    # ---------------- 2. Metallic Face Mask Isolation ----------------
    face_mask = np.zeros(gray.shape, dtype=np.uint8)
    cv2.drawContours(face_mask, [contour], -1, 255, -1)
    # Strip outer boundary ring by 14px to eliminate bevel and chamfer edge transitions
    cv2.drawContours(face_mask, [contour], -1, 0, 14)

    if hole_circle is not None:
        hx, hy, hr = int(hole_circle[0]), int(hole_circle[1]), int(hole_circle[2])
        cv2.circle(face_mask, (hx, hy), int(hr + 14), 0, -1)
    else:
        # Fallback inner hole mask from center
        (cx, cy), r = cv2.minEnclosingCircle(contour)
        cv2.circle(face_mask, (int(cx), int(cy)), int(r * 0.55), 0, -1)

    total_face_pixels = np.count_nonzero(face_mask)

    if total_face_pixels > 150:
        face_roi = cv2.bitwise_and(gray, gray, mask=face_mask)

        # ---------------- 3. Surface Scratches and Cracks ----------------
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        lap_abs = np.uint8(np.absolute(laplacian))
        _, scratch_bin = cv2.threshold(lap_abs, lap_thresh, 255, cv2.THRESH_BINARY)
        scratch_bin = cv2.bitwise_and(scratch_bin, scratch_bin, mask=face_mask)

        defect_pixels = np.count_nonzero(scratch_bin)
        defect_fraction = defect_pixels / float(total_face_pixels)

        if defect_pixels >= min_scratch_px and defect_fraction > max_defect_frac:
            defects.append(
                f"[Surface] Scratch/crack pattern: {defect_pixels} defect pixels on face ({defect_fraction * 100:.1f}%)"
            )

        # ---------------- 4. Discoloration & Corrosion Patches ----------------
        mean_val, std_val = cv2.meanStdDev(face_roi, mask=face_mask)
        intensity_variance = float(std_val[0][0])
        if intensity_variance > variance_limit:
            defects.append(
                f"[Finish] Surface discoloration/corrosion: variance {intensity_variance:.1f} indicates uneven coating"
            )

        # ---------------- 5. Dark Pit & Chip Mark Detection ----------------
        mean_intensity = float(mean_val[0][0])
        pit_thresh = max(20, int(mean_intensity * 0.35))
        _, dark_pits = cv2.threshold(face_roi, pit_thresh, 255, cv2.THRESH_BINARY_INV)
        dark_pits = cv2.bitwise_and(dark_pits, dark_pits, mask=face_mask)
        pit_pixels = np.count_nonzero(dark_pits)
        pit_frac = pit_pixels / float(total_face_pixels)

        # Localized pitting: between 3% and 18% of face (if >18%, it's central hole shadow, not pit)
        if (0.035 * tol_mult) < pit_frac < 0.18:
            defects.append(f"[Surface] Cavitation/pitting detected ({pit_pixels} px, {pit_frac*100:.1f}%)")

        # ---------------- 6. Material Alloy Hue & Reflectance Verification ----------------
        if color_img is not None and len(color_img.shape) == 3:
            b_ch, g_ch, r_ch = cv2.split(color_img)
            mean_b = float(np.mean(b_ch[face_mask > 0]))
            mean_r = float(np.mean(r_ch[face_mask > 0]))
            if not config.HARDWARE_SIMULATION_MODE and metal_type == "brass":
                if mean_b > 0 and (mean_r / mean_b) < 1.10:
                    defects.append(f"[Alloy] Hue anomaly: brass requires warm golden spectrum (R/B > 1.10)")

    return {
        "defects": defects,
        "has_defects": len(defects) > 0,
        "defect_count": len(defects)
    }
