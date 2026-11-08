"""
Inspectra - Dataset Sample Generator
Generates synthetic realistic images of nuts and washers (normal and defective)
at 0° and 90° angles, as well as laser line triangulation profile frames.
"""

import os
import math
import numpy as np
import cv2

def create_nut_image(size=(480, 640), angle_deg=0, defective=False, inner_r=41, outer_r=88):
    """Generate a realistic image of a hexagonal nut on a dark industrial background."""
    img = np.full((size[0], size[1], 3), 32, dtype=np.uint8)
    center = (size[1] // 2, size[0] // 2)
    
    # 6 vertices for hexagonal nut
    pts = []
    base_angle = math.radians(angle_deg)
    for i in range(6):
        a = base_angle + i * (2 * math.pi / 6)
        x = int(center[0] + outer_r * math.cos(a))
        y = int(center[1] + outer_r * math.sin(a))
        pts.append((x, y))
    pts = np.array(pts, dtype=np.int32)

    # Metallic nut body
    cv2.fillPoly(img, [pts], (185, 190, 195))
    cv2.polylines(img, [pts], True, (220, 225, 230), 2)

    # Inner circular hole
    cv2.circle(img, center, inner_r, (28, 28, 30), -1)
    cv2.circle(img, center, inner_r, (130, 130, 135), 2)
    
    # Subtle thread ridges
    for r in range(inner_r - 4, inner_r, 2):
        cv2.circle(img, center, r, (40, 40, 45), 1)

    if defective:
        # Sharp scratch across one face
        p1 = (center[0] + 15, center[1] - 45)
        p2 = (center[0] + 65, center[1] - 25)
        cv2.line(img, p1, p2, (20, 20, 25), 3)
        cv2.line(img, (p1[0]+1, p1[1]+1), (p2[0]+1, p2[1]+1), (250, 250, 250), 1)
        # Burr / chip
        cv2.circle(img, (center[0] - 50, center[1] + 35), 8, (15, 15, 20), -1)

    return img

def create_washer_image(size=(480, 640), angle_deg=0, defective=False, inner_r=44, outer_r=100):
    """Generate a realistic image of a circular washer."""
    img = np.full((size[0], size[1], 3), 32, dtype=np.uint8)
    center = (size[1] // 2, size[0] // 2)

    cv2.circle(img, center, outer_r, (185, 190, 195), -1)
    cv2.circle(img, center, outer_r, (220, 225, 230), 2)

    # Inner hole
    cv2.circle(img, center, inner_r, (28, 28, 30), -1)
    cv2.circle(img, center, inner_r, (130, 130, 135), 2)

    if defective:
        # Burr / irregularity on edge
        burr_angle = math.radians(angle_deg + 45)
        bx = int(center[0] + outer_r * math.cos(burr_angle))
        by = int(center[1] + outer_r * math.sin(burr_angle))
        cv2.circle(img, (bx, by), 14, (110, 110, 115), -1)
        # Deep surface crack
        c1 = (center[0] - 45, center[1] - 15)
        c2 = (center[0] - 80, center[1] + 15)
        cv2.line(img, c1, c2, (20, 20, 25), 3)

    return img

def create_laser_frame(size=(480, 640), has_component=True, height_bump_mm=4.0):
    """Generate a red laser line profile frame across an inspected part."""
    frame = np.full((size[0], size[1], 3), 15, dtype=np.uint8)
    # Baseline laser stripe at y=240
    base_y = 240
    laser_color = (40, 40, 255) # Bright red in BGR
    core_color = (200, 200, 255)

    comp_start = 220
    comp_end = 420

    for x in range(size[1]):
        y = base_y
        if has_component and comp_start <= x <= comp_end:
            # Triangulation shift upwards proportional to height
            shift = int(height_bump_mm * 15.0 * math.sin((x - comp_start) / (comp_end - comp_start) * math.pi))
            y = base_y - shift

        # Draw laser line with Gaussian thickness
        for dy in range(-3, 4):
            ny = np.clip(y + dy, 0, size[0] - 1)
            weight = math.exp(-0.5 * (dy / 1.2)**2)
            for c in range(3):
                val = int(laser_color[c] * weight + (core_color[c] if abs(dy) <= 1 else 0))
                frame[ny, x, c] = max(frame[ny, x, c], min(255, val))

    return frame

def generate_all():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ds_dir = os.path.join(base_dir, "dataset")
    os.makedirs(os.path.join(ds_dir, "nuts"), exist_ok=True)
    os.makedirs(os.path.join(ds_dir, "washers"), exist_ok=True)
    os.makedirs(os.path.join(ds_dir, "pass"), exist_ok=True)
    os.makedirs(os.path.join(ds_dir, "fail"), exist_ok=True)
    os.makedirs(os.path.join(ds_dir, "laser"), exist_ok=True)

    # 1. Nut 0 deg & 90 deg pass
    n0 = create_nut_image(angle_deg=0, defective=False)
    n90 = create_nut_image(angle_deg=90, defective=False)
    cv2.imwrite(os.path.join(ds_dir, "nuts", "nut_pass_0deg.jpg"), n0)
    cv2.imwrite(os.path.join(ds_dir, "nuts", "nut_pass_90deg.jpg"), n90)
    cv2.imwrite(os.path.join(ds_dir, "pass", "nut_0deg.jpg"), n0)
    cv2.imwrite(os.path.join(ds_dir, "pass", "nut_90deg.jpg"), n90)

    # 2. Nut defective
    n_fail0 = create_nut_image(angle_deg=0, defective=True)
    n_fail90 = create_nut_image(angle_deg=90, defective=True)
    cv2.imwrite(os.path.join(ds_dir, "nuts", "nut_fail_0deg.jpg"), n_fail0)
    cv2.imwrite(os.path.join(ds_dir, "nuts", "nut_fail_90deg.jpg"), n_fail90)
    cv2.imwrite(os.path.join(ds_dir, "fail", "nut_fail_0deg.jpg"), n_fail0)
    cv2.imwrite(os.path.join(ds_dir, "fail", "nut_fail_90deg.jpg"), n_fail90)

    # 3. Washer pass
    w0 = create_washer_image(angle_deg=0, defective=False)
    w90 = create_washer_image(angle_deg=90, defective=False)
    cv2.imwrite(os.path.join(ds_dir, "washers", "washer_pass_0deg.jpg"), w0)
    cv2.imwrite(os.path.join(ds_dir, "washers", "washer_pass_90deg.jpg"), w90)
    cv2.imwrite(os.path.join(ds_dir, "pass", "washer_0deg.jpg"), w0)
    cv2.imwrite(os.path.join(ds_dir, "pass", "washer_90deg.jpg"), w90)

    # 4. Washer defective
    w_fail0 = create_washer_image(angle_deg=0, defective=True)
    w_fail90 = create_washer_image(angle_deg=90, defective=True)
    cv2.imwrite(os.path.join(ds_dir, "washers", "washer_fail_0deg.jpg"), w_fail0)
    cv2.imwrite(os.path.join(ds_dir, "washers", "washer_fail_90deg.jpg"), w_fail90)
    cv2.imwrite(os.path.join(ds_dir, "fail", "washer_fail_0deg.jpg"), w_fail0)
    cv2.imwrite(os.path.join(ds_dir, "fail", "washer_fail_90deg.jpg"), w_fail90)

    # 5. Laser frames
    l_flat = create_laser_frame(has_component=False)
    l_pass = create_laser_frame(has_component=True, height_bump_mm=3.2)
    l_fail = create_laser_frame(has_component=True, height_bump_mm=8.5) # out of tolerance
    cv2.imwrite(os.path.join(ds_dir, "laser", "laser_baseline.jpg"), l_flat)
    cv2.imwrite(os.path.join(ds_dir, "laser", "laser_pass.jpg"), l_pass)
    cv2.imwrite(os.path.join(ds_dir, "laser", "laser_fail.jpg"), l_fail)

    print("Successfully generated all sample datasets in", ds_dir)

if __name__ == "__main__":
    generate_all()

