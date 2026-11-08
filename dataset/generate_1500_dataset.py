"""
Inspectra - Comprehensive Industrial Dataset Generator (1,500 Images)
Generates 1,500 photorealistic annotated images of M3 to M8 Nuts and Washers:
- Sizes: M3, M4, M5, M6, M8 (150 images each for Nuts & Washers = 750 + 750 = 1,500 total)
- Inclined camera perspective: 45° tilt (with realistic ±3° optical variation)
- Full rotation angles: 0° to 360°
- Realistic metallic materials: Carbon Steel, Stainless 316, Galvanized Zinc, Brass
- Ground-truth defect variations: Nominal (PASS), Scratch, Burr, Pitting, Off-center hole, Thread damage, Out-of-tolerance
- Bounding box annotations (YOLO format) and full metadata manifest (labels.json)
"""

import os
import math
import json
import random
import time
from typing import Tuple, Dict, Any, List
import numpy as np
import cv2

# Metric Standards Lookup Table (DIN 934 for Nuts, DIN 125 for Washers)
ISO_SPECS = {
    "nut": {
        "M3": {"flats_mm": 5.5, "corners_mm": 6.01, "inner_mm": 2.8, "thickness_mm": 2.4, "tol_outer": 0.35, "tol_inner": 0.35},
        "M4": {"flats_mm": 7.0, "corners_mm": 7.66, "inner_mm": 3.7, "thickness_mm": 3.2, "tol_outer": 0.35, "tol_inner": 0.35},
        "M5": {"flats_mm": 8.0, "corners_mm": 8.79, "inner_mm": 4.6, "thickness_mm": 4.0, "tol_outer": 0.40, "tol_inner": 0.40},
        "M6": {"flats_mm": 10.0, "corners_mm": 11.05, "inner_mm": 5.5, "thickness_mm": 5.0, "tol_outer": 0.45, "tol_inner": 0.45},
        "M8": {"flats_mm": 13.0, "corners_mm": 14.38, "inner_mm": 7.4, "thickness_mm": 6.5, "tol_outer": 0.50, "tol_inner": 0.50},
    },
    "washer": {
        "M3": {"outer_mm": 7.0, "inner_mm": 3.2, "thickness_mm": 0.5, "tol_outer": 0.35, "tol_inner": 0.30},
        "M4": {"outer_mm": 9.0, "inner_mm": 4.3, "thickness_mm": 0.8, "tol_outer": 0.35, "tol_inner": 0.35},
        "M5": {"outer_mm": 10.0, "inner_mm": 5.3, "thickness_mm": 1.0, "tol_outer": 0.40, "tol_inner": 0.40},
        "M6": {"outer_mm": 12.0, "inner_mm": 6.4, "thickness_mm": 1.6, "tol_outer": 0.45, "tol_inner": 0.45},
        "M8": {"outer_mm": 16.0, "inner_mm": 8.4, "thickness_mm": 1.6, "tol_outer": 0.50, "tol_inner": 0.50},
    }
}

MM_PER_PIXEL = 0.12 # Calibrated scale: 1 mm ≈ 8.33 pixels

MATERIAL_TONES = {
    "carbon_steel": (170, 175, 180),
    "stainless_316": (205, 210, 215),
    "galvanized": (185, 195, 200),
    "brass": (100, 180, 215) # BGR
}

def apply_perspective_tilt(img: np.ndarray, tilt_deg: float = 45.0) -> np.ndarray:
    """Simulate camera viewing angle (45 degrees from conveyor normal)."""
    h, w = img.shape[:2]
    src = np.float32([[0, 0], [w, 0], [w, h], [0, h]])
    
    # Foreshortening along vertical Y axis: cos(tilt_deg)
    cos_theta = math.cos(math.radians(tilt_deg))
    margin_x = int(w * 0.08 * (1.0 - cos_theta))
    pad_y = int(h * (1.0 - cos_theta) * 0.5)

    dst = np.float32([
        [margin_x, pad_y],
        [w - margin_x, pad_y],
        [w, h - pad_y],
        [0, h - pad_y]
    ])
    M = cv2.getPerspectiveTransform(src, dst)
    warped = cv2.warpPerspective(img, M, (w, h), borderValue=(28, 28, 30))
    return warped

def inject_defects(img: np.ndarray, center: Tuple[int, int], radius: int, defects: list):
    """Render physical defects: scratches, edge burrs, pitting, cracks."""
    for d in defects:
        if d == "scratch":
            # Linear high-contrast scratch across component face
            p1 = (center[0] + random.randint(-radius, radius), center[1] + random.randint(-radius, radius))
            p2 = (center[0] + random.randint(-radius, radius), center[1] + random.randint(-radius, radius))
            cv2.line(img, p1, p2, (240, 245, 250), thickness=random.randint(1, 2))
            cv2.line(img, (p1[0]+1, p1[1]+1), (p2[0]+1, p2[1]+1), (60, 60, 65), thickness=1)
        elif d == "pitting":
            # Corrosion / pitting cluster
            for _ in range(random.randint(6, 14)):
                px = center[0] + int(random.uniform(-radius*0.7, radius*0.7))
                py = center[1] + int(random.uniform(-radius*0.7, radius*0.7))
                cv2.circle(img, (px, py), random.randint(1, 3), (40, 42, 45), -1)
                cv2.circle(img, (px+1, py), 1, (130, 135, 140), 1)
        elif d == "burr":
            # Edge defect / protrusion
            ba = random.uniform(0, 2 * math.pi)
            bx = int(center[0] + radius * math.cos(ba))
            by = int(center[1] + radius * math.sin(ba))
            cv2.circle(img, (bx, by), random.randint(3, 6), (195, 200, 205), -1)
            cv2.circle(img, (bx, by), random.randint(3, 6), (50, 50, 55), 1)
        elif d == "notch_crack":
            # Edge notch / fracture line
            ba = random.uniform(0, 2 * math.pi)
            bx1 = int(center[0] + radius * math.cos(ba))
            by1 = int(center[1] + radius * math.sin(ba))
            bx2 = int(center[0] + (radius - 12) * math.cos(ba))
            by2 = int(center[1] + (radius - 12) * math.sin(ba))
            cv2.line(img, (bx1, by1), (bx2, by2), (20, 20, 22), 2)

def generate_photorealistic_nut(
    size_label="M5",
    rotation_deg=0,
    defects=None,
    tilt_deg=45.0,
    material="carbon_steel",
    canvas_size=(480, 640)
) -> Tuple[np.ndarray, dict]:
    """Generate industrial-grade hex nut image."""
    if defects is None:
        defects = []
    
    spec = ISO_SPECS["nut"][size_label]
    corners_mm = spec["corners_mm"]
    flats_mm = spec["flats_mm"]
    inner_mm = spec["inner_mm"]

    # Introduce slight tolerance perturbation
    if "oversized" in defects:
        corners_mm += 1.2
        flats_mm += 1.0
    elif "undersized" in defects:
        corners_mm -= 1.0
        flats_mm -= 0.9

    outer_r = int((corners_mm / 2.0) / MM_PER_PIXEL)
    inner_r = int((inner_mm / 2.0) / MM_PER_PIXEL)

    # Base conveyor canvas with industrial matte surface
    img = np.full((canvas_size[0], canvas_size[1], 3), 32, dtype=np.uint8)
    noise = np.random.normal(0, 2.5, img.shape).astype(np.int16)
    img = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)

    center = (canvas_size[1] // 2 + random.randint(-8, 8), canvas_size[0] // 2 + random.randint(-8, 8))
    hole_center = list(center)
    if "eccentric_hole" in defects:
        hole_center[0] += random.choice([-1, 1]) * int(outer_r * 0.22)
        hole_center[1] += random.choice([-1, 1]) * int(outer_r * 0.22)

    base_tone = MATERIAL_TONES.get(material, (180, 185, 190))

    # 6 vertices for regular hexagon
    base_angle = math.radians(rotation_deg)
    pts = []
    for i in range(6):
        a = base_angle + i * (2.0 * math.pi / 6.0)
        x = int(center[0] + outer_r * math.cos(a))
        y = int(center[1] + outer_r * math.sin(a))
        pts.append((x, y))
    pts = np.array(pts, dtype=np.int32)

    # Base polygon fill
    cv2.fillPoly(img, [pts], base_tone)

    # Metallic facet directional shading
    for i in range(6):
        p1 = pts[i]
        p2 = pts[(i + 1) % 6]
        mid = ((p1[0] + p2[0]) // 2, (p1[1] + p2[1]) // 2)
        facet_angle = math.atan2(mid[1] - center[1], mid[0] - center[0])
        light_factor = math.cos(facet_angle - 2.2) # Key light at 126°
        shade = int(base_tone[0] + light_factor * 26)
        shade = max(110, min(240, shade))
        facet_poly = np.array([p1, p2, center], dtype=np.int32)
        cv2.fillPoly(img, [facet_poly], (shade, shade + 3, shade + 5))

    # Outer facet edges & chamfer highlight
    cv2.polylines(img, [pts], True, (230, 235, 240), 2)

    # Inner threaded hole
    cv2.circle(img, tuple(hole_center), inner_r, (25, 26, 28), -1)
    # Thread grooves
    if "thread_damage" not in defects:
        for r_th in range(inner_r - 2, max(2, inner_r - 6), -2):
            cv2.circle(img, tuple(hole_center), r_th, (65, 68, 72), 1)
    else:
        # Burr inside thread
        cv2.line(img, (hole_center[0] - inner_r + 2, hole_center[1]), 
                 (hole_center[0] - inner_r + 8, hole_center[1] + 3), (180, 185, 190), 2)

    # Chamfer ring around hole
    cv2.circle(img, tuple(hole_center), inner_r + 2, (150, 155, 160), 1)

    # Inject any surface/edge defects
    inject_defects(img, center, outer_r, defects)

    # Apply 45° perspective tilt simulation
    warped = apply_perspective_tilt(img, tilt_deg=tilt_deg)

    # Ground truth data
    is_pass = len(defects) == 0
    gt = {
        "component_type": "nut",
        "metric_size": size_label,
        "corners_mm": round(corners_mm, 2),
        "flats_mm": round(flats_mm, 2),
        "inner_mm": round(inner_mm, 2),
        "status": "PASS" if is_pass else "FAIL",
        "defects": defects,
        "tilt_deg": tilt_deg,
        "material": material,
        "rotation_deg": rotation_deg
    }
    return warped, gt

def generate_photorealistic_washer(
    size_label="M5",
    rotation_deg=0,
    defects=None,
    tilt_deg=45.0,
    material="carbon_steel",
    canvas_size=(480, 640)
) -> Tuple[np.ndarray, dict]:
    """Generate industrial-grade circular flat washer image."""
    if defects is None:
        defects = []

    spec = ISO_SPECS["washer"][size_label]
    outer_mm = spec["outer_mm"]
    inner_mm = spec["inner_mm"]

    if "oversized" in defects:
        outer_mm += 1.5
    elif "undersized" in defects:
        outer_mm -= 1.2

    outer_r = int((outer_mm / 2.0) / MM_PER_PIXEL)
    inner_r = int((inner_mm / 2.0) / MM_PER_PIXEL)

    img = np.full((canvas_size[0], canvas_size[1], 3), 32, dtype=np.uint8)
    noise = np.random.normal(0, 2.5, img.shape).astype(np.int16)
    img = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)

    center = (canvas_size[1] // 2 + random.randint(-8, 8), canvas_size[0] // 2 + random.randint(-8, 8))
    hole_center = list(center)
    if "eccentric_hole" in defects:
        hole_center[0] += random.choice([-1, 1]) * int(outer_r * 0.25)
        hole_center[1] += random.choice([-1, 1]) * int(outer_r * 0.25)

    base_tone = MATERIAL_TONES.get(material, (185, 190, 195))

    # Outer circle
    cv2.circle(img, center, outer_r, base_tone, -1)

    # Concentric turned finish / circular brush texture
    for rad in range(inner_r + 4, outer_r - 2, 4):
        shade_offset = random.randint(-12, 12)
        r_tone = (
            max(90, min(240, base_tone[0] + shade_offset)),
            max(90, min(240, base_tone[1] + shade_offset)),
            max(90, min(240, base_tone[2] + shade_offset))
        )
        cv2.circle(img, center, rad, r_tone, 1)

    # Specular highlight streak across face
    ang_rad = math.radians(rotation_deg + 45)
    p_spec1 = (int(center[0] - outer_r * math.cos(ang_rad)), int(center[1] - outer_r * math.sin(ang_rad)))
    p_spec2 = (int(center[0] + outer_r * math.cos(ang_rad)), int(center[1] + outer_r * math.sin(ang_rad)))
    cv2.line(img, p_spec1, p_spec2, (230, 235, 240), 3)

    # Outer perimeter edge ring
    cv2.circle(img, center, outer_r, (215, 220, 225), 1)

    # Inner circular punch hole (dark)
    cv2.circle(img, tuple(hole_center), inner_r, (25, 26, 28), -1)
    # Inner stamped edge bevel
    cv2.circle(img, tuple(hole_center), inner_r, (140, 145, 150), 1)

    # Inject any surface/edge defects
    inject_defects(img, center, outer_r, defects)

    # Apply 45° perspective tilt simulation
    warped = apply_perspective_tilt(img, tilt_deg=tilt_deg)

    is_pass = len(defects) == 0
    gt = {
        "component_type": "washer",
        "metric_size": size_label,
        "outer_mm": round(outer_mm, 2),
        "inner_mm": round(inner_mm, 2),
        "status": "PASS" if is_pass else "FAIL",
        "defects": defects,
        "tilt_deg": tilt_deg,
        "material": material,
        "rotation_deg": rotation_deg
    }
    return warped, gt

def build_yolo_annotation(class_idx: int, center_x: float, center_y: float, width: float, height: float, img_w=640, img_h=480) -> str:
    """Format YOLO bounding box (class x_center y_center width height normalized)."""
    xc = max(0.0, min(1.0, center_x / img_w))
    yc = max(0.0, min(1.0, center_y / img_h))
    w = max(0.0, min(1.0, width / img_w))
    h = max(0.0, min(1.0, height / img_h))
    return f"{class_idx} {xc:.6f} {yc:.6f} {w:.6f} {h:.6f}\n"

def generate_1500_dataset():
    """Build the full 1500 image dataset for M3 to M8 Nuts and Washers."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    subdirs = [
        "nuts", "washers", "pass", "fail",
        "train/nuts", "train/washers",
        "test/nuts", "test/washers",
        "yolo_labels"
    ]
    for sub in subdirs:
        os.makedirs(os.path.join(base_dir, sub), exist_ok=True)

    sizes = ["M3", "M4", "M5", "M6", "M8"]
    materials = ["carbon_steel", "stainless_316", "galvanized", "brass"]
    defect_pool = [
        [], # PASS
        [], # PASS
        ["scratch"],
        ["burr"],
        ["pitting"],
        ["notch_crack"],
        ["eccentric_hole"],
        ["oversized"],
        ["undersized"]
    ]

    total_images = 1500
    images_per_category = total_images // 2 # 750 nuts, 750 washers
    images_per_size = images_per_category // len(sizes) # 150 images per size (M3..M8)

    print(f"Generating {total_images} industrial images (750 Nuts, 750 Washers across M3-M8)...")
    t0 = time.time()
    manifest = []
    
    # 1. GENERATE NUTS (750 images: 150 of each M3, M4, M5, M6, M8)
    img_counter = 0
    for size_label in sizes:
        for idx in range(images_per_size):
            img_counter += 1
            rot = (idx * 23 + random.randint(0, 15)) % 360
            tilt = 45.0 + random.uniform(-2.5, 2.5) # ~45° realistic tilt
            mat = materials[idx % len(materials)]
            defects = list(defect_pool[idx % len(defect_pool)])
            if "thread_damage" in defect_pool and idx % 9 == 0:
                defects.append("thread_damage")

            img, gt = generate_photorealistic_nut(
                size_label=size_label,
                rotation_deg=rot,
                defects=defects,
                tilt_deg=tilt,
                material=mat
            )

            status_str = "pass" if gt["status"] == "PASS" else "fail"
            fname = f"nut_{size_label}_{status_str}_{idx:03d}.jpg"
            gt["filename"] = fname

            # Save full resolution JPEG
            full_path = os.path.join(base_dir, "nuts", fname)
            cv2.imwrite(full_path, img, [cv2.IMWRITE_JPEG_QUALITY, 92])

            # Class folder (pass or fail)
            cv2.imwrite(os.path.join(base_dir, status_str, fname), img, [cv2.IMWRITE_JPEG_QUALITY, 90])

            # Train / Test split (80% train, 20% test)
            split = "train" if (idx % 5 != 0) else "test"
            gt["split"] = split
            cv2.imwrite(os.path.join(base_dir, split, "nuts", fname), img, [cv2.IMWRITE_JPEG_QUALITY, 90])

            # YOLO annotation (Class 0: Nut)
            bb_w = int(gt["corners_mm"] / MM_PER_PIXEL * 1.3)
            bb_h = int(bb_w * math.cos(math.radians(tilt)) * 1.3)
            yolo_txt = build_yolo_annotation(0, 320, 240, bb_w, bb_h)
            with open(os.path.join(base_dir, "yolo_labels", fname.replace(".jpg", ".txt")), "w") as f:
                f.write(yolo_txt)

            manifest.append(gt)

    # 2. GENERATE WASHERS (750 images: 150 of each M3, M4, M5, M6, M8)
    for size_label in sizes:
        for idx in range(images_per_size):
            img_counter += 1
            rot = (idx * 29 + random.randint(0, 15)) % 360
            tilt = 45.0 + random.uniform(-2.5, 2.5)
            mat = materials[idx % len(materials)]
            defects = list(defect_pool[idx % len(defect_pool)])

            img, gt = generate_photorealistic_washer(
                size_label=size_label,
                rotation_deg=rot,
                defects=defects,
                tilt_deg=tilt,
                material=mat
            )

            status_str = "pass" if gt["status"] == "PASS" else "fail"
            fname = f"washer_{size_label}_{status_str}_{idx:03d}.jpg"
            gt["filename"] = fname

            full_path = os.path.join(base_dir, "washers", fname)
            cv2.imwrite(full_path, img, [cv2.IMWRITE_JPEG_QUALITY, 92])

            cv2.imwrite(os.path.join(base_dir, status_str, fname), img, [cv2.IMWRITE_JPEG_QUALITY, 90])

            split = "train" if (idx % 5 != 0) else "test"
            gt["split"] = split
            cv2.imwrite(os.path.join(base_dir, split, "washers", fname), img, [cv2.IMWRITE_JPEG_QUALITY, 90])

            # YOLO annotation (Class 1: Washer)
            bb_w = int(gt["outer_mm"] / MM_PER_PIXEL * 1.25)
            bb_h = int(bb_w * math.cos(math.radians(tilt)) * 1.25)
            yolo_txt = build_yolo_annotation(1, 320, 240, bb_w, bb_h)
            with open(os.path.join(base_dir, "yolo_labels", fname.replace(".jpg", ".txt")), "w") as f:
                f.write(yolo_txt)

            manifest.append(gt)

    # Save complete JSON manifest
    manifest_path = os.path.join(base_dir, "labels.json")
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    # YOLO classes list
    with open(os.path.join(base_dir, "classes.txt"), "w") as f:
        f.write("nut\nwasher\n")

    elapsed = round(time.time() - t0, 2)
    print(f"DONE: Generated {len(manifest)} images in {elapsed}s.")
    print(f"Manifest written to: {manifest_path}")

if __name__ == "__main__":
    generate_1500_dataset()
