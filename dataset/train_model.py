"""
Inspectra - Machine Learning Training Pipeline for M3-M8 Nuts & Washers
Trains:
1. Component Classifier (Nut vs Washer)
2. Metric Size Classifier (M3, M4, M5, M6, M8)
3. Precision Dimension Regressor (Predicts outer/flats mm & inner hole mm with 45° tilt compensation)

Uses the 1,500 labeled images dataset, extracts geometric perspective-resilient features,
trains scikit-learn Random Forest classifiers/regressors, and saves models to backend/models/.
"""

import os
import json
import math
import time
import joblib
import cv2
import numpy as np
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import classification_report, accuracy_score, r2_score, mean_absolute_error

MM_PER_PIXEL = 0.12 # Calibrated scale

def extract_features_from_image(img_path: str, tilt_deg: float = 45.0) -> np.ndarray:
    """
    Extract geometric & perspective-corrected features from 45°-tilted image.
    Features:
    [0]  Rectified Major Axis (px)
    [1]  Rectified Minor Axis (px)
    [2]  Aspect Ratio (Major / Minor)
    [3]  Rectified Area (px^2)
    [4]  Rectified Perimeter (px)
    [5]  Rectified Circularity (4 * pi * Area / P^2)
    [6]  Corner Count (approxPolyDP on rectified contour)
    [7]  Hexagonal Angular Variance (deviation from 60° spacing)
    [8]  Radial Harmonic Variance (std(r) / mean(r)) - ~0.01 for washers, ~0.15 for nuts
    [9]  Inner Hole Detected (1.0 or 0.0)
    [10] Inner Hole Major Axis (px)
    [11] Inner / Outer Ratio
    [12] Hole Eccentricity (px)
    """
    img = cv2.imread(img_path)
    if img is None:
        return np.zeros(13, dtype=np.float32)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    _, thresh = cv2.threshold(blurred, 60, 255, cv2.THRESH_BINARY)

    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return np.zeros(13, dtype=np.float32)

    c = max(contours, key=cv2.contourArea)
    if cv2.contourArea(c) < 300:
        return np.zeros(13, dtype=np.float32)

    # 1. Perspective Rectification along 45° tilt axis
    # Foreshortened vertical axis is scaled by 1 / cos(tilt_deg)
    cos_tilt = math.cos(math.radians(tilt_deg))
    scale_y = 1.0 / cos_tilt if cos_tilt > 0.1 else 1.4142

    m = cv2.moments(c)
    cx = m["m10"] / m["m00"] if m["m00"] > 0 else 320.0
    cy = m["m01"] / m["m00"] if m["m00"] > 0 else 240.0

    # Un-warp contour points to orthogonal 0° space
    pts_rect = []
    for pt in c:
        px, py = pt[0]
        ry = (py - cy) * scale_y + cy
        pts_rect.append([[px, ry]])
    pts_rect = np.array(pts_rect, dtype=np.float32)
    c_rect = np.int32(pts_rect)

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

    # Corner count on rectified contour
    best_corners = cv2.approxPolyDP(c_rect, 0.035 * perim_rect, True)
    corner_count = len(best_corners)

    # Hexagonal angular regularity
    hex_ang_var = 1.0
    if corner_count == 6:
        c_pts = [p[0] for p in best_corners]
        angles = sorted([math.atan2(p[1] - cy, p[0] - cx) for p in c_pts])
        diffs = [(angles[(i + 1) % 6] - angles[i]) % (2 * math.pi) for i in range(6)]
        hex_ang_var = float(np.mean([abs(d - (math.pi / 3.0)) for d in diffs]))

    # Radial variance from centroid
    radii = [math.hypot(p[0][0] - cx, p[0][1] - cy) for p in c_rect]
    rad_mean = np.mean(radii) if radii else 1.0
    rad_std = np.std(radii) if radii else 0.0
    rad_var_ratio = rad_std / rad_mean if rad_mean > 0 else 0.0

    # Inner hole detection
    mask = np.zeros(gray.shape, dtype=np.uint8)
    cv2.drawContours(mask, [c], -1, 255, -1)
    inv = cv2.bitwise_not(gray)
    inv_masked = cv2.bitwise_and(inv, inv, mask=mask)
    _, h_thresh = cv2.threshold(inv_masked, 180, 255, cv2.THRESH_BINARY)
    h_contours, _ = cv2.findContours(h_thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    has_hole = 0.0
    hole_major_px = 0.0
    eccentricity_px = 0.0
    if h_contours:
        lh = max(h_contours, key=cv2.contourArea)
        if len(lh) >= 5 and cv2.contourArea(lh) > 80:
            (hcx, hcy), (hd1, hd2), _ = cv2.fitEllipse(lh)
            # Rectify hole major/minor
            hole_major_px = max(hd1, hd2)
            has_hole = 1.0
            eccentricity_px = math.hypot(hcx - cx, (hcy - cy) * scale_y)

    inner_outer_ratio = hole_major_px / major_px if major_px > 0 else 0.0

    return np.array([
        major_px,
        minor_px,
        aspect_ratio,
        area_rect,
        perim_rect,
        circ_rect,
        corner_count,
        hex_ang_var,
        rad_var_ratio,
        has_hole,
        hole_major_px,
        inner_outer_ratio,
        eccentricity_px
    ], dtype=np.float32)

def train_and_evaluate():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    labels_file = os.path.join(base_dir, "labels.json")
    with open(labels_file, "r") as f:
        metadata = json.load(f)

    print(f"Loading {len(metadata)} samples from manifest...")
    t0 = time.time()

    X_train, y_type_train, y_size_train, y_dim_train = [], [], [], []
    X_test, y_type_test, y_size_test, y_dim_test = [], [], [], []

    size_map = {"M3": 0, "M4": 1, "M5": 2, "M6": 3, "M8": 4}
    inv_size_map = {v: k for k, v in size_map.items()}

    for item in metadata:
        fname = item["filename"]
        comp_dir = "nuts" if item["component_type"] == "nut" else "washers"
        img_path = os.path.join(base_dir, comp_dir, fname)
        if not os.path.exists(img_path):
            continue

        feats = extract_features_from_image(img_path, tilt_deg=item.get("tilt_deg", 45.0))
        
        # Ground truths
        is_washer = 1 if item["component_type"] == "washer" else 0
        size_idx = size_map.get(item["metric_size"], 2)
        
        # Dimension ground truth [outer_mm, inner_mm]
        if item["component_type"] == "nut":
            outer_mm = item["flats_mm"]
            inner_mm = item["inner_mm"]
        else:
            outer_mm = item["outer_mm"]
            inner_mm = item["inner_mm"]
        dim_target = [outer_mm, inner_mm]

        if item.get("split") == "test":
            X_test.append(feats)
            y_type_test.append(is_washer)
            y_size_test.append(size_idx)
            y_dim_test.append(dim_target)
        else:
            X_train.append(feats)
            y_type_train.append(is_washer)
            y_size_train.append(size_idx)
            y_dim_train.append(dim_target)

    X_train = np.array(X_train)
    y_type_train = np.array(y_type_train)
    y_size_train = np.array(y_size_train)
    y_dim_train = np.array(y_dim_train)

    X_test = np.array(X_test)
    y_type_test = np.array(y_type_test)
    y_size_test = np.array(y_size_test)
    y_dim_test = np.array(y_dim_test)

    print(f"Features extracted in {round(time.time() - t0, 2)}s. Train: {len(X_train)}, Test: {len(X_test)}")

    # 1. Train Component Type Classifier (Nut vs Washer)
    print("\nTraining Component Type Classifier (Nut vs Washer)...")
    clf_type = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
    clf_type.fit(X_train, y_type_train)
    pred_type = clf_type.predict(X_test)
    acc_type = accuracy_score(y_type_test, pred_type)
    print(f"Component Type Accuracy: {acc_type * 100:.2f}%")
    print(classification_report(y_type_test, pred_type, target_names=["Nut", "Washer"]))

    # 2. Train Metric Size Classifier (M3, M4, M5, M6, M8)
    print("\nTraining Metric Size Classifier (M3 to M8)...")
    clf_size = RandomForestClassifier(n_estimators=120, max_depth=12, random_state=42)
    clf_size.fit(X_train, y_size_train)
    pred_size = clf_size.predict(X_test)
    acc_size = accuracy_score(y_size_test, pred_size)
    print(f"Metric Size Accuracy: {acc_size * 100:.2f}%")
    print(classification_report(y_size_test, pred_size, target_names=list(size_map.keys())))

    # 3. Train Dimension Regressor [outer_mm, inner_mm]
    print("\nTraining Precision Dimension Regressor...")
    reg_dim = RandomForestRegressor(n_estimators=100, max_depth=12, random_state=42)
    reg_dim.fit(X_train, y_dim_train)
    pred_dim = reg_dim.predict(X_test)
    mae_outer = mean_absolute_error(y_dim_test[:, 0], pred_dim[:, 0])
    mae_inner = mean_absolute_error(y_dim_test[:, 1], pred_dim[:, 1])
    r2 = r2_score(y_dim_test, pred_dim)
    print(f"Dimension Prediction R2 Score: {r2:.4f}")
    print(f"Mean Absolute Error Outer: {mae_outer:.3f} mm")
    print(f"Mean Absolute Error Inner: {mae_inner:.3f} mm")

    # Save Models and Manifest to backend/models/
    models_dir = os.path.join(os.path.dirname(base_dir), "backend", "models")
    os.makedirs(models_dir, exist_ok=True)
    bundle_path = os.path.join(models_dir, "component_size_bundle.pkl")

    model_bundle = {
        "clf_type": clf_type,
        "clf_size": clf_size,
        "reg_dim": reg_dim,
        "size_map": size_map,
        "inv_size_map": inv_size_map,
        "metrics": {
            "type_accuracy": round(float(acc_type), 4),
            "size_accuracy": round(float(acc_size), 4),
            "mae_outer_mm": round(float(mae_outer), 4),
            "mae_inner_mm": round(float(mae_inner), 4),
            "r2_score": round(float(r2), 4)
        },
        "trained_at": time.strftime("%Y-%m-%d %H:%M:%S")
    }

    joblib.dump(model_bundle, bundle_path)
    print(f"\nModel bundle saved successfully to: {bundle_path}")

    # Write metrics summary JSON
    metrics_path = os.path.join(models_dir, "model_metrics.json")
    with open(metrics_path, "w") as f:
        json.dump(model_bundle["metrics"], f, indent=2)

if __name__ == "__main__":
    train_and_evaluate()

