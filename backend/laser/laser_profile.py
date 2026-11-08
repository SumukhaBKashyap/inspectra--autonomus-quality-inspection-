"""
Inspectra - Laser Line Sub-pixel Extraction
Extracts the bright red laser stripe across image columns using intensity-weighted centroids.
"""

from typing import Tuple
import cv2
import numpy as np

def extract_laser_line_profile(frame: np.ndarray) -> np.ndarray:
    """
    Extract sub-pixel vertical centroid of the laser line for each column.
    Returns:
        1D array of centroids (row indices) per column. NaN where no laser line is detected.
    """
    if len(frame.shape) == 3:
        # Use a combination of intensity and red prominence
        r = frame[:, :, 2].astype(np.float32)
        g = frame[:, :, 1].astype(np.float32)
        b = frame[:, :, 0].astype(np.float32)
        # Red enhancement + intensity
        laser_map = np.clip(0.6 * r + 0.4 * (r - np.maximum(g, b)), 0, 255).astype(np.uint8)
    else:
        laser_map = frame.copy()

    h, w = laser_map.shape
    centroids = np.full(w, np.nan, dtype=np.float64)

    # Adaptive / Otsu or threshold at 25
    _, mask = cv2.threshold(laser_map, 25, 255, cv2.THRESH_BINARY)

    for col in range(w):
        col_vals = laser_map[:, col].astype(np.float64)
        col_mask = mask[:, col]
        active_rows = np.where(col_mask > 0)[0]
        if len(active_rows) >= 1:
            weights = col_vals[active_rows]
            total_w = np.sum(weights)
            if total_w > 0:
                centroids[col] = np.sum(active_rows * weights) / total_w

    return centroids

def build_reference_baseline(width: int, default_row: float = 240.0) -> np.ndarray:
    """Expected laser line row position on the bare platform without a component."""
    return np.full(width, default_row, dtype=np.float64)
