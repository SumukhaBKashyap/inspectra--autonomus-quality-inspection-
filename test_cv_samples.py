"""Test all 17 real sample images through the CV pipeline and report results."""
import sys
import os
import json
import math

# Add backend parent to path so 'backend' is a package
sys.path.insert(0, r"d:\inspectra")

import cv2
import numpy as np

# Import using full package path
from backend.vision.preprocessing import preprocess_image
from backend.vision.component_detection import find_primary_contour, classify_component
from backend.vision.dimension_measurement import measure_dimensions_precise
from backend.vision.defect_detection import detect_surface_defects_precise

sample_dir = r"d:\inspectra\media\test_samples"
results = []

for i in range(17):
    img_path = os.path.join(sample_dir, f"page{i}_img0.jpeg")
    if not os.path.exists(img_path):
        print(f"[page{i}] IMAGE NOT FOUND")
        continue

    img = cv2.imread(img_path)
    h, w = img.shape[:2]
    print(f"\n{'='*70}")
    print(f"[page{i}] Size: {w}x{h}")

    norm_gray, binary = preprocess_image(img)
    contour = find_primary_contour(binary)

    if contour is None:
        print(f"  -> NO CONTOUR DETECTED")
        results.append({"page": i, "status": "NO_CONTOUR"})
        continue

    contour_area = cv2.contourArea(contour)
    print(f"  Contour area: {contour_area:.0f} px")

    classification = classify_component(contour, norm_gray)
    comp_type = classification["component_type"]
    metric_size = classification.get("metric_size", "UNKNOWN")
    confidence = classification["confidence"]
    circularity = classification["circularity"]
    corners = classification["corners"]
    has_hole = classification["has_hole"]
    hole_circle = classification.get("hole_circle")

    print(f"  Type: {comp_type} | Size: {metric_size} | Confidence: {confidence}")
    print(f"  Circularity: {circularity} | Corners: {corners} | Hole: {has_hole}")
    if hole_circle:
        print(f"  Hole circle: cx={hole_circle[0]:.1f}, cy={hole_circle[1]:.1f}, r={hole_circle[2]:.1f}")

    dim_data = measure_dimensions_precise(
        contour, norm_gray, comp_type,
        corner_points=classification.get("corner_points"),
        hole_circle=hole_circle,
        hole_eccentricity_px=classification.get("hole_eccentricity_px", 0.0),
        metric_size=metric_size
    )

    print(f"  Outer diameter: {dim_data['outer_diameter_mm']} mm")
    print(f"  Across flats:   {dim_data['across_flats_mm']} mm")
    print(f"  Inner diameter: {dim_data['inner_diameter_mm']} mm")
    print(f"  Required outer: {dim_data['required_outer_mm']} +/- {dim_data['required_tolerance_mm']} mm")
    print(f"  Required inner: {dim_data['required_inner_mm']} +/- {dim_data['required_tolerance_mm']} mm")
    print(f"  Measured outer (effective): {dim_data['measured_outer_mm']} mm")
    print(f"  Deviation outer: {dim_data['deviation_outer_mm']} mm -> {dim_data['outer_status']}")
    print(f"  Deviation inner: {dim_data['deviation_inner_mm']} mm -> {dim_data['inner_status']}")
    print(f"  Within tolerance: {dim_data['is_within_tolerance']}")
    if dim_data['dimensional_flags']:
        for f in dim_data['dimensional_flags']:
            print(f"  FLAG: {f}")

    defect_data = detect_surface_defects_precise(
        contour, norm_gray, binary,
        hole_circle=hole_circle,
        color_img=img
    )
    
    from backend.vision.multi_angle import inspect_single_view
    view_res = inspect_single_view(img, angle_label=f"sample_{i}")
    view_status = view_res["status"]

    print(f"  Defects ({len(defect_data['defects'])}): {defect_data['defects']}")
    print(f"  >>> FINAL STATUS: {view_status}")

    results.append({
        "page": i,
        "type": comp_type,
        "size": metric_size,
        "confidence": confidence,
        "circularity": circularity,
        "corners": corners,
        "outer_mm": dim_data['outer_diameter_mm'],
        "flats_mm": dim_data['across_flats_mm'],
        "inner_mm": dim_data['inner_diameter_mm'],
        "measured_outer": dim_data['measured_outer_mm'],
        "dev_outer": dim_data['deviation_outer_mm'],
        "dev_inner": dim_data['deviation_inner_mm'],
        "dim_pass": dim_data['is_within_tolerance'],
        "defects": defect_data["defects"],
        "dim_flags": dim_data["dimensional_flags"],
        "status": view_status
    })

print(f"\n\n{'='*70}")
print("SUMMARY")
print(f"{'='*70}")
pass_count = sum(1 for r in results if r.get("status") == "PASS")
fail_count = sum(1 for r in results if r.get("status") == "FAIL")
no_contour = sum(1 for r in results if r.get("status") == "NO_CONTOUR")
print(f"PASS: {pass_count} | FAIL: {fail_count} | NO_CONTOUR: {no_contour} | Total: {len(results)}")
print()

# Print compact table
print(f"{'Page':>5} {'Type':>7} {'Size':>4} {'MeasOut':>8} {'InnerMM':>8} {'DevOut':>7} {'DevIn':>7} {'#Def':>5} {'Status':>6}")
for r in results:
    if r.get("status") == "NO_CONTOUR":
        print(f"{r['page']:>5} {'---':>7} {'---':>4} {'---':>8} {'---':>8} {'---':>7} {'---':>7} {'---':>5} {'NOCNT':>6}")
    else:
        n_def = len(r.get("defects", []))
        print(f"{r['page']:>5} {r['type']:>7} {r['size']:>4} {r['measured_outer']:>8} {r['inner_mm']:>8} {r['dev_outer']:>7} {r['dev_inner']:>7} {n_def:>5} {r['status']:>6}")
