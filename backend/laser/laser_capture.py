"""
Inspectra - Laser Profile Capture Module
Acquires the laser triangulation frame from the inspection camera or dataset sample.
"""

import os
from typing import Optional
import cv2
import numpy as np
from ..config import config

def capture_laser_frame(is_defective: bool = False) -> np.ndarray:
    """
    Capture a frame showing the projected red laser line across the component.
    Uses real camera frame if connected, or dataset/synthetic laser image.
    """
    if not config.HARDWARE_SIMULATION_MODE:
        from ..vision.camera import camera_manager
        frame = camera_manager.get_frame()
        if frame is not None:
            return frame

    # Load from dataset
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    filename = "laser_fail.jpg" if is_defective else "laser_pass.jpg"
    path = os.path.join(base_dir, "dataset", "laser", filename)

    if os.path.exists(path):
        img = cv2.imread(path)
        if img is not None:
            return img

    from dataset.generate_samples import create_laser_frame
    return create_laser_frame(has_component=True, height_bump_mm=7.5 if is_defective else 3.5)

