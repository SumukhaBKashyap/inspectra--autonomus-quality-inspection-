"""
Inspectra - Comprehensive Industrial Quality Dataset Generator
Generates high-precision realistic synthetic dataset of nuts and washers:
- Multiple rotation angles (0°, 15°, 30°, 45°, 60°, 75°, 90°, 120°, 150°, 180°)
- Camera perspective angle simulation (45°-60° tilt)
- Realistic metallic materials (galvanized steel, machined alloy, chamfers, threads)
- Multiple defect types (scratches, pits, edge burrs, thread damage, dimensional variance, hole eccentricity)
- Ground truth annotations saved to labels.json and YOLO bbox format (.txt)
"""

import os
import math
import json
import random
import numpy as np
import cv2

def apply_perspective_tilt(img: np.ndarray, tilt_deg: float = 50.0) -> np.ndarray:
    """Simulate camera viewing angle (45-60 degrees from vertical)."""
    h, w = img.shape[:2]
    # Perspective transform matrix
    src = np.float32([[0, 0], [w, 0], [w, h], [0, h]])
    # Tilt compresses along vertical axis and expands slightly at bottom
    compression = math.sin(math.radians(tilt_deg))
    margin_x = int(w * 0.06 * (1.0 - compression))
    pad_y = int(h * (1.0 - compression) * 0.4)

    dst = np.float32([
        [margin_x, pad_y],
        [w - margin_x, pad_y],
        [w, h - pad_y],
        [0, h - pad_y]
    ])
    M = cv2.getPerspectiveTransform(src, dst)
    warped = cv2.warpPerspective(img, M, (w, h), borderValue=(30, 30, 30))
    return warped

def create_photorealistic_nut(
    size=(480, 640),
    rotation_deg=0,
    outer_r=88, # ~21.1 mm @ 0.12 mm/px
    inner_r=41, # ~9.8 mm
    defects=None,
    tilt_deg=0.0,
    metallic_tone=(185, 190, 195)
):
    """Generate high-precision nut image with metallic sheen, chamfers, and threads."""
    if defects is None:
        defects = []
    
    img = np.full((size[0], size[1], 3), 32, dtype=np.uint8)
    # Background industrial texture
    bg_noise = np.random.normal(0, 3, img.shape).astype(np.int16)
    img = np.clip(img.astype(np.int16) + bg_noise, 0, 255).astype(np.uint8)

    center = [size[1] // 2, size[0] // 2]
    
    # Check for hole eccentricity defect
    hole_center = list(center)
    if "eccentric_hole" in defects:
        hole_center[0] += 8
        hole_center[1] -= 6

    # 6 vertices for hexagonal nut
    pts = []
    base_angle = math.radians(rotation_deg)
    for i in range(6):
        a = base_angle + i * (2 * math.pi / 6)
        x = int(center[0] + outer_r * math.cos(a))
        y = int(center[1] + outer_r * math.sin(a))
        pts.append((x, y))
    pts = np.array(pts, dtype=np.int32)

    # Base nut body fill
    cv2.fillPoly(img, [pts], metallic_tone)

    # Bevel shading across facets
    for i in range(6):
        p1 = pts[i]
        p2 = pts[(i + 1) % 6]
        # facet midpoint
        mid = ((p1[0] + p2[0]) // 2, (p1[1] + p2[1]) // 2)
        facet_angle = math.atan2(mid[1] - center[1], mid[0] - center[0])
        # Lighting from top-left (angle ~ 2.3 rad)
        light_factor = math.cos(facet_angle - 2.3)
        shade = int(metallic_tone[0] + light_factor * 20)
        shade = max(140, min(225, shade))
        facet_poly = np.array([p1, p2, center], dtype=np.int32)
        cv2.fillPoly(img, [facet_poly], (shade, shade + 3, shade + 6))

    # Outer facet edges & chamfer highlight
    cv2.polylines(img, [pts], True, (225, 230, 235), 2)

    # Inner circular hole (dark platform background)
    cv2.circle(img, tuple(hole_center), inner_r, (25, 25, 28), -1)
    # Inner chamfer ring
    cv2.circle(img, tuple(hole_center), inner_r, (140, 145, 150), 2)

    # Inner thread texture
    if "thread_damage" not in defects:
        for r in range(inner_r - 6, inner_r, 2):
            cv2.circle(img, tuple(hole_center), r, (40, 42, 46), 1)
    else:
        # Mangled inner thread
        for r in range(inner_r - 6, inner_r, 2):
            cv2.ellipse(img, tuple(hole_center), (r, r - 3), 45, 0, 280, (60, 62, 66), 1)

    # ---------------- Injected Defects ----------------
    if "scratch" in defects:
        p1 = (center[0] + int(outer_r * 0.2), center[1] - int(outer_r * 0.5))
        p2 = (center[0] + int(outer_r * 0.7), center[1] - int(outer_r * 0.2))
        cv2.line(img, p1, p2, (20, 20, 25), 3)
        cv2.line(img, (p1[0] + 1, p1[1] + 1), (p2[0] + 1, p2[1] + 1), (250, 250, 250), 1)

    if "cross_scratch" in defects:
        p1 = (center[0] - int(outer_r * 0.6), center[1] - int(outer_r * 0.3))
        p2 = (center[0] - int(outer_r * 0.2), center[1] + int(outer_r * 0.5))
        cv2.line(img, p1, p2, (18, 18, 22), 2)
        p3 = (center[0] - int(outer_r * 0.6), center[1] + int(outer_r * 0.2))
        p4 = (center[0] - int(outer_r * 0.2), center[1] - int(outer_r * 0.4))
        cv2.line(img, p3, p4, (18, 18, 22), 2)

    if "burr" in defects:
        burr_angle = base_angle + math.pi / 3
        bx = int(center[0] + outer_r * math.cos(burr_angle))
        by = int(center[1] + outer_r * math.sin(burr_angle))
        cv2.circle(img, (bx, by), 12, (170, 175, 180), -1)
        cv2.circle(img, (bx, by), 12, (225, 230, 235), 2)

    if "chip_pit" in defects:
        pit_x = center[0] - int(outer_r * 0.55)
        pit_y = center[1] + int(outer_r * 0.35)
        cv2.circle(img, (pit_x, pit_y), 7, (18, 18, 22), -1)
        cv2.circle(img, (pit_x + 1, pit_y + 1), 7, (230, 230, 230), 1)

    if "discoloration" in defects:
        spot_center = (center[0] + int(outer_r * 0.4), center[1] + int(outer_r * 0.3))
        overlay = img.copy()
        cv2.circle(overlay, spot_center, 22, (50, 60, 75), -1)
        cv2.addWeighted(overlay, 0.45, img, 0.55, 0, img)

    if tilt_deg > 0:
        img = apply_perspective_tilt(img, tilt_deg)

    return img

def create_photorealistic_washer(
    size=(480, 640),
    rotation_deg=0,
    outer_r=100, # ~24.0 mm @ 0.12 mm/px
    inner_r=44,  # ~10.5 mm
    defects=None,
    tilt_deg=0.0,
    metallic_tone=(185, 190, 195)
):
    """Generate high-precision circular washer image with concentric machining lines."""
    if defects is None:
        defects = []

    img = np.full((size[0], size[1], 3), 32, dtype=np.uint8)
    bg_noise = np.random.normal(0, 3, img.shape).astype(np.int16)
    img = np.clip(img.astype(np.int16) + bg_noise, 0, 255).astype(np.uint8)

    center = [size[1] // 2, size[0] // 2]

    hole_center = list(center)
    if "eccentric_hole" in defects:
        hole_center[0] += 10
        hole_center[1] += 5

    # Base washer disc
    cv2.circle(img, tuple(center), outer_r, metallic_tone, -1)
    
    # Radial sheen & concentric lathe machining marks
    for r in range(inner_r + 4, outer_r - 2, 4):
        cv2.circle(img, tuple(center), r, (metallic_tone[0] - 6, metallic_tone[1] - 4, metallic_tone[2] - 2), 1)

    # Outer bevel and rim
    cv2.circle(img, tuple(center), outer_r, (225, 230, 235), 2)

    # Inner circular hole
    cv2.circle(img, tuple(hole_center), inner_r, (25, 25, 28), -1)
    cv2.circle(img, tuple(hole_center), inner_r, (140, 145, 150), 2)

    # ---------------- Injected Defects ----------------
    if "scratch" in defects:
        p1 = (center[0] - int(outer_r * 0.7), center[1] + int(outer_r * 0.2))
        p2 = (center[0] - int(outer_r * 0.3), center[1] + int(outer_r * 0.5))
        cv2.line(img, p1, p2, (20, 20, 25), 3)
        cv2.line(img, (p1[0] + 1, p1[1] + 1), (p2[0] + 1, p2[1] + 1), (250, 250, 250), 1)

    if "burr" in defects:
        burr_angle = math.radians(rotation_deg + 45)
        bx = int(center[0] + outer_r * math.cos(burr_angle))
        by = int(center[1] + outer_r * math.sin(burr_angle))
        cv2.circle(img, (bx, by), 14, (180, 185, 190), -1)
        cv2.circle(img, (bx, by), 14, (230, 235, 240), 2)

    if "notch_crack" in defects:
        c1 = (center[0] + int(outer_r * 0.8), center[1] - int(outer_r * 0.2))
        c2 = (center[0] + int(outer_r * 0.5), center[1] - int(outer_r * 0.1))
        cv2.line(img, c1, c2, (15, 15, 20), 3)

    if "corrosion" in defects:
        spot_center = (center[0] - int(outer_r * 0.4), center[1] - int(outer_r * 0.3))
        overlay = img.copy()
        cv2.circle(overlay, spot_center, 25, (45, 55, 70), -1)
        cv2.addWeighted(overlay, 0.5, img, 0.5, 0, img)

    if tilt_deg > 0:
        img = apply_perspective_tilt(img, tilt_deg)

    return img

def build_yolo_annotation(comp_type: str, center=(320, 240), bbox_w=190, bbox_h=190, img_w=640, img_h=480):
    """Format: <class-index> <x_center> <y_center> <width> <height> (normalized 0-1)"""
    cls_idx = 0 if comp_type == "nut" else 1
    return f"{cls_idx} {center[0]/img_w:.6f} {center[1]/img_h:.6f} {bbox_w/img_w:.6f} {bbox_h/img_h:.6f}\n"

def generate_full_dataset():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ds_dir = os.path.join(base_dir, "dataset")

    dirs = [
        os.path.join(ds_dir, "nuts"),
        os.path.join(ds_dir, "washers"),
        os.path.join(ds_dir, "pass"),
        os.path.join(ds_dir, "fail"),
        os.path.join(ds_dir, "train", "nuts"),
        os.path.join(ds_dir, "train", "washers"),
        os.path.join(ds_dir, "test", "nuts"),
        os.path.join(ds_dir, "test", "washers"),
        os.path.join(ds_dir, "yolo_labels"),
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)

    metadata = []
    
    # Standard angles for multi-angle testing
    angles = [0, 15, 30, 45, 60, 75, 90, 120, 135, 150, 180, 225, 270]

    print("Generating comprehensive dataset...")

    # 1. GENERATE NUTS (PASS & DEFECTIVE)
    for idx, angle in enumerate(angles):
        # Pass Nut
        nut_pass = create_photorealistic_nut(rotation_deg=angle, defects=[], outer_r=88, inner_r=41)
        name_pass = f"nut_pass_{angle}deg.jpg"
        p_path = os.path.join(ds_dir, "nuts", name_pass)
        cv2.imwrite(p_path, nut_pass)
        cv2.imwrite(os.path.join(ds_dir, "pass", f"nut_{angle}deg.jpg"), nut_pass)
        
        # Split into train/test
        sub = "train" if (idx % 3 != 0) else "test"
        cv2.imwrite(os.path.join(ds_dir, sub, "nuts", name_pass), nut_pass)

        # YOLO label
        lbl_pass = build_yolo_annotation("nut", center=(320, 240), bbox_w=185, bbox_h=185)
        with open(os.path.join(ds_dir, "yolo_labels", name_pass.replace(".jpg", ".txt")), "w") as f:
            f.write(lbl_pass)

        metadata.append({
            "filename": name_pass,
            "component_type": "nut",
            "angle_deg": angle,
            "status": "PASS",
            "defects": [],
            "outer_diameter_mm": 21.12,
            "inner_diameter_mm": 9.84,
            "split": sub
        })

        # Defective Nuts (varying defect types)
        defect_options = [["scratch"], ["burr"], ["chip_pit"], ["discoloration"], ["cross_scratch"], ["eccentric_hole"]]
        chosen_defect = defect_options[idx % len(defect_options)]
        
        # Undersized/oversized for some
        r_out = 88
        if idx == 2: r_out = 105 # Out-of-tolerance oversized
        if idx == 5: r_out = 72  # Out-of-tolerance undersized

        nut_fail = create_photorealistic_nut(rotation_deg=angle, defects=chosen_defect, outer_r=r_out, inner_r=41)
        name_fail = f"nut_fail_{chosen_defect[0]}_{angle}deg.jpg"
        f_path = os.path.join(ds_dir, "nuts", name_fail)
        cv2.imwrite(f_path, nut_fail)
        cv2.imwrite(os.path.join(ds_dir, "fail", name_fail), nut_fail)
        cv2.imwrite(os.path.join(ds_dir, sub, "nuts", name_fail), nut_fail)

        lbl_fail = build_yolo_annotation("nut", center=(320, 240), bbox_w=int(r_out * 2.1), bbox_h=int(r_out * 2.1))
        with open(os.path.join(ds_dir, "yolo_labels", name_fail.replace(".jpg", ".txt")), "w") as f:
            f.write(lbl_fail)

        metadata.append({
            "filename": name_fail,
            "component_type": "nut",
            "angle_deg": angle,
            "status": "FAIL",
            "defects": chosen_defect,
            "outer_diameter_mm": round(r_out * 0.12 * 2, 2),
            "inner_diameter_mm": 9.84,
            "split": sub
        })

    # 2. GENERATE WASHERS (PASS & DEFECTIVE)
    for idx, angle in enumerate(angles):
        # Pass Washer
        w_pass = create_photorealistic_washer(rotation_deg=angle, defects=[], outer_r=100, inner_r=44)
        name_pass = f"washer_pass_{angle}deg.jpg"
        p_path = os.path.join(ds_dir, "washers", name_pass)
        cv2.imwrite(p_path, w_pass)
        cv2.imwrite(os.path.join(ds_dir, "pass", f"washer_{angle}deg.jpg"), w_pass)

        sub = "train" if (idx % 3 != 0) else "test"
        cv2.imwrite(os.path.join(ds_dir, sub, "washers", name_pass), w_pass)

        lbl_pass = build_yolo_annotation("washer", center=(320, 240), bbox_w=205, bbox_h=205)
        with open(os.path.join(ds_dir, "yolo_labels", name_pass.replace(".jpg", ".txt")), "w") as f:
            f.write(lbl_pass)

        metadata.append({
            "filename": name_pass,
            "component_type": "washer",
            "angle_deg": angle,
            "status": "PASS",
            "defects": [],
            "outer_diameter_mm": 24.0,
            "inner_diameter_mm": 10.56,
            "split": sub
        })

        # Defective Washers
        w_defect_options = [["scratch"], ["burr"], ["notch_crack"], ["corrosion"], ["eccentric_hole"]]
        w_chosen = w_defect_options[idx % len(w_defect_options)]
        
        r_out = 100
        if idx == 1: r_out = 118 # Out-of-tolerance oversized
        if idx == 4: r_out = 82  # Out-of-tolerance undersized

        w_fail = create_photorealistic_washer(rotation_deg=angle, defects=w_chosen, outer_r=r_out, inner_r=44)
        name_fail = f"washer_fail_{w_chosen[0]}_{angle}deg.jpg"
        f_path = os.path.join(ds_dir, "washers", name_fail)
        cv2.imwrite(f_path, w_fail)
        cv2.imwrite(os.path.join(ds_dir, "fail", name_fail), w_fail)
        cv2.imwrite(os.path.join(ds_dir, sub, "washers", name_fail), w_fail)

        lbl_fail = build_yolo_annotation("washer", center=(320, 240), bbox_w=int(r_out * 2.05), bbox_h=int(r_out * 2.05))
        with open(os.path.join(ds_dir, "yolo_labels", name_fail.replace(".jpg", ".txt")), "w") as f:
            f.write(lbl_fail)

        metadata.append({
            "filename": name_fail,
            "component_type": "washer",
            "angle_deg": angle,
            "status": "FAIL",
            "defects": w_chosen,
            "outer_diameter_mm": round(r_out * 0.12 * 2, 2),
            "inner_diameter_mm": 10.56,
            "split": sub
        })

    # Save manifest
    manifest_path = os.path.join(ds_dir, "labels.json")
    with open(manifest_path, "w") as f:
        json.dump(metadata, f, indent=2)

    # YOLO class names file
    with open(os.path.join(ds_dir, "classes.txt"), "w") as f:
        f.write("nut\nwasher\n")

    print(f"Successfully generated {len(metadata)} labeled images with YOLO annotations in {ds_dir}")

if __name__ == "__main__":
    generate_full_dataset()

