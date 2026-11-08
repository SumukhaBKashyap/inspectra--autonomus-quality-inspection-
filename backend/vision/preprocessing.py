"""
Inspectra - High-Precision Computer Vision Preprocessing Module
Converts raw component images into normalized, edge-preserving filtered grayscale
and clean binary masks with illumination correction.
"""

from typing import Tuple, Optional, Dict, Any
import cv2
import numpy as np

def preprocess_image(img: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    Apply edge-preserving bilateral filtering, CLAHE illumination correction,
    and Otsu morphological thresholding.
    Returns:
        norm_gray: Illumination-normalized grayscale image
        binary: Clean binary mask of the outer component
    """
    if len(img.shape) == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        gray = img.copy()

    # 1. Edge-preserving bilateral filter: removes high-frequency sensor noise
    # while keeping sharp chamfers, facet corners, and scratch boundaries intact
    filtered = cv2.bilateralFilter(gray, d=7, sigmaColor=35, sigmaSpace=35)

    # 2. CLAHE (Contrast Limited Adaptive Histogram Equalization)
    clahe = cv2.createCLAHE(clipLimit=2.2, tileGridSize=(8, 8))
    norm_gray = clahe.apply(filtered)

    # 3. Gaussian smoothing for robust thresholding
    blurred = cv2.GaussianBlur(norm_gray, (5, 5), 0)

    # 4. Otsu's thresholding
    _, binary = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # Ensure component is white (255) and background is black (0)
    if np.sum(binary == 255) > (binary.size * 0.65):
        binary = cv2.bitwise_not(binary)

    # 5. Morphological closing to seal internal body facet seams
    kernel_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel_close, iterations=2)

    # 6. Morphological opening to eliminate fine peripheral dust artifacts
    kernel_open = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel_open, iterations=1)

    return norm_gray, binary

def extract_edge_map(norm_gray: np.ndarray, low_thresh: int = 50, high_thresh: int = 150) -> np.ndarray:
    """Extract sub-pixel Canny edge map for precision boundary and defect analysis."""
    return cv2.Canny(norm_gray, low_thresh, high_thresh)
