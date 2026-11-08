"""Analyze actual pixel sizes of components in test images to calibrate mm_per_pixel."""
import sys, os
sys.path.insert(0, r"d:\inspectra")
import cv2
import numpy as np
from backend.vision.preprocessing import preprocess_image
from backend.vision.component_detection import find_primary_contour

sample_dir = r"d:\inspectra\media\test_samples"

print(f"{'Page':>5} {'ImgWxH':>12} {'ContArea':>10} {'MajAxis':>8} {'MinAxis':>8} {'Circ':>6} {'EncR':>6}")
for i in range(17):
    img = cv2.imread(os.path.join(sample_dir, f"page{i}_img0.jpeg"))
    h, w = img.shape[:2]
    norm_gray, binary = preprocess_image(img)
    contour = find_primary_contour(binary)
    if contour is None:
        print(f"{i:>5} {f'{w}x{h}':>12} {'NONE':>10}")
        continue
    area = cv2.contourArea(contour)
    _, enc_r = cv2.minEnclosingCircle(contour)
    if len(contour) >= 5:
        _, (ax1, ax2), _ = cv2.fitEllipse(contour)
        major = max(ax1, ax2)
        minor = min(ax1, ax2)
    else:
        major = minor = enc_r * 2
    circ = (4.0 * np.pi * area) / (cv2.arcLength(contour, True) ** 2)
    print(f"{i:>5} {f'{w}x{h}':>12} {area:>10.0f} {major:>8.1f} {minor:>8.1f} {circ:>6.3f} {enc_r:>6.1f}")

    # Also check what fraction of image the contour covers
    img_area = w * h
    fill_pct = (area / img_area) * 100
    print(f"      fill={fill_pct:.1f}% of image | diameter_px={major:.0f}px")

