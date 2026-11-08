"""
Inspectra - Configurable Settings, Material Profiles, and Thresholds
Supports runtime updates from the frontend settings panel,
environment variable overrides, and persistent settings JSON.
"""

import os
import json
from typing import Dict, Any

SETTINGS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings.json")

# Material Profiles Specification
METAL_PROFILES = {
    "carbon_steel": {
        "name": "Carbon Steel (Grade 8.8 / 10.9)",
        "short_name": "Carbon Steel",
        "category": "Ferromagnetic",
        "permeability_ur": 180.0,
        "conductivity_iacs": 14.5,
        "eddy_nominal_impedance": 50.0, # Ohms
        "eddy_frequency_khz": 50,
        "eddy_phase_deg": 48.0,
        "eddy_tolerance_pct": 10.0,
        "color_tone_rgb": (140, 145, 150),
        "reflectance_factor": 0.70,
        "laser_roughness_mm": 0.80,
        "description": "Standard high-tensile structural fastener steel with strong magnetic permeability."
    },
    "stainless_steel": {
        "name": "Stainless Steel (AISI 304 / 316)",
        "short_name": "Stainless Steel",
        "category": "Austenitic / Non-magnetic",
        "permeability_ur": 1.02,
        "conductivity_iacs": 3.1,
        "eddy_nominal_impedance": 85.0, # Ohms
        "eddy_frequency_khz": 200,
        "eddy_phase_deg": 76.0,
        "eddy_tolerance_pct": 12.0,
        "color_tone_rgb": (205, 210, 215),
        "reflectance_factor": 0.95,
        "laser_roughness_mm": 0.65,
        "description": "Corrosion-resistant austenitic stainless steel with low electrical conductivity."
    },
    "aluminum": {
        "name": "Aluminum Alloy (6061-T6)",
        "short_name": "Aluminum Alloy",
        "category": "Non-ferrous / Conductive",
        "permeability_ur": 1.00,
        "conductivity_iacs": 43.0,
        "eddy_nominal_impedance": 28.0, # Ohms
        "eddy_frequency_khz": 100,
        "eddy_phase_deg": 24.0,
        "eddy_tolerance_pct": 8.0,
        "color_tone_rgb": (215, 220, 225),
        "reflectance_factor": 0.90,
        "laser_roughness_mm": 0.65,
        "description": "High-conductivity non-ferrous alloy requiring high phase sensitivity."
    },
    "brass": {
        "name": "Brass / Copper Alloy (C36000)",
        "short_name": "Brass Alloy",
        "category": "Non-ferrous / Machinable",
        "permeability_ur": 1.00,
        "conductivity_iacs": 26.5,
        "eddy_nominal_impedance": 36.0, # Ohms
        "eddy_frequency_khz": 80,
        "eddy_phase_deg": 35.0,
        "eddy_tolerance_pct": 9.0,
        "color_tone_rgb": (195, 165, 95),
        "reflectance_factor": 0.85,
        "laser_roughness_mm": 0.65,
        "description": "Free-cutting brass with characteristic golden tone and medium-high conductivity."
    },
    "galvanized_steel": {
        "name": "Galvanized / Zinc-Plated Steel",
        "short_name": "Galvanized Steel",
        "category": "Coated Ferromagnetic",
        "permeability_ur": 140.0,
        "conductivity_iacs": 22.0,
        "eddy_nominal_impedance": 44.0, # Ohms
        "eddy_frequency_khz": 60,
        "eddy_phase_deg": 42.0,
        "eddy_tolerance_pct": 11.0,
        "color_tone_rgb": (160, 165, 170),
        "reflectance_factor": 0.75,
        "laser_roughness_mm": 0.85,
        "description": "Carbon steel core with electroplated or hot-dip protective zinc coating layer."
    }
}

# Inspection Analysis Modes
ANALYSIS_MODES = {
    "standard": {
        "name": "Standard Industrial Quality",
        "description": "ISO 4032 / ISO 7089 commercial fastener specifications",
        "tolerance_multiplier": 1.0,
        "cv_defect_area_limit": 0.025,
        "eddy_tolerance_multiplier": 1.0,
        "laser_tolerance_multiplier": 1.0
    },
    "aerospace": {
        "name": "High-Precision Aerospace Grade",
        "description": "Strict AS9100 / MIL-SPEC tolerances with micro-defect rejection",
        "tolerance_multiplier": 0.65,
        "cv_defect_area_limit": 0.012,
        "eddy_tolerance_multiplier": 0.75,
        "laser_tolerance_multiplier": 0.65
    },
    "high_speed": {
        "name": "High-Speed Bulk Sorting",
        "description": "Fast line-rate sorting focused on geometric classification and major defects",
        "tolerance_multiplier": 1.35,
        "cv_defect_area_limit": 0.05,
        "eddy_tolerance_multiplier": 1.30,
        "laser_tolerance_multiplier": 1.30
    }
}

# Default configuration dictionary
DEFAULT_CONFIG = {
    # System Operational Mode: "manual" or "automated"
    "OPERATION_MODE": "automated",

    # Active Conveyor Material & Analysis Selection
    "SELECTED_METAL": "carbon_steel",
    "ANALYSIS_TYPE": "standard",

    # System & Hardware Mode
    "HARDWARE_SIMULATION_MODE": True,
    
    # Camera Configuration (Android IP Webcam / USB / RTSP)
    "CAMERA_SOURCE": "http://192.168.1.100:8080/video",
    "CAMERA_SNAPSHOT_URL": "http://192.168.1.100:8080/shot.jpg",
    "CAMERA_ANGLE_DEG": 50.0,
    "CAMERA_FPS": 30,
    "CAMERA_WIDTH": 640,
    "CAMERA_HEIGHT": 480,

    # Arduino Serial Communication
    "SERIAL_PORT": "COM3",
    "BAUD_RATE": 115200,
    "SERIAL_TIMEOUT": 2.0,
    "SERVO_ACK_TIMEOUT": 6.0,
    "ARRIVAL_TIMEOUT": 20.0,

    # Servo Calibration Angles (SG90 degrees)
    "SERVO1_REST_ANGLE": 0,
    "SERVO1_ROTATE_ANGLE": 90,
    "SERVO2_REST_ANGLE": 0,
    "SERVO2_PUSH_ANGLE": 65,
    "SERVO3_NEUTRAL_ANGLE": 90,
    "SERVO3_NUT_ANGLE": 45,
    "SERVO3_WASHER_ANGLE": 135,

    # Computer Vision (REAL)
    "CV_MIN_CONTOUR_AREA": 600,
    "CV_CIRCULARITY_THRESHOLD": 0.78,
    "CV_NUT_MIN_CORNERS": 5,
    "CV_MM_PER_PIXEL": 0.12,
    "CV_CALIBRATED": True,
    "CV_MAX_DEFECT_FRACTION": 0.025,
    
    # Base Reference Tolerances (mm) - scaled by analysis mode
    "NUT_TARGET_OUTER_MM": 21.0,
    "NUT_TOLERANCE_OUTER_MM": 1.2,
    "NUT_TARGET_INNER_MM": 10.0,
    "NUT_TOLERANCE_INNER_MM": 1.2,
    
    "WASHER_TARGET_OUTER_MM": 24.0,
    "WASHER_TOLERANCE_OUTER_MM": 1.5,
    "WASHER_TARGET_INNER_MM": 10.5,
    "WASHER_TOLERANCE_INNER_MM": 0.8,

    # Operator Dashboard Required Dimensions (Pass/Fail Calibration)
    "REQUIRED_OUTER_MM": 10.0,
    "REQUIRED_INNER_MM": 5.0,
    "REQUIRED_TOLERANCE_MM": 0.45,
    "CALIBRATION_PRESET": "M5",

    # Triangular Laser Profiling (REAL)
    "LASER_ANGLE_DEG": 35.0,
    "LASER_STAND_OFF_MM": 120.0,
    "LASER_PX_PITCH_MM": 0.045,
    "LASER_CALIBRATED": True,
    "LASER_MAX_HEIGHT_VARIATION_MM": 0.65,
    "LASER_ANOMALY_FRACTION_THRESHOLD": 0.08,

    # Eddy Current Inspection
    "EDDY_NOMINAL_IMPEDANCE": 50.0,
    "EDDY_ANOMALY_THRESHOLD": 0.10,

    # Central Decision Engine Rules
    "DECISION_FAIL_ON_CV_DEFECTS": True,
    "DECISION_FAIL_ON_LASER_ANOMALY": True,
    "DECISION_FAIL_ON_EDDY_ANOMALY": True,
    "DECISION_REVIEW_ON_UNKNOWN_TYPE": True,
    "DECISION_REVIEW_ON_MISSING_DATA": True,
}

class AppConfig:
    def __init__(self):
        self._config = DEFAULT_CONFIG.copy()
        self.load()

    def load(self):
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "r") as f:
                    saved = json.load(f)
                    self._config.update(saved)
            except Exception as e:
                print(f"[Config] Error loading settings.json: {e}")

    def save(self):
        try:
            with open(SETTINGS_FILE, "w") as f:
                json.dump(self._config, f, indent=2)
        except Exception as e:
            print(f"[Config] Error saving settings.json: {e}")

    def get(self, key: str, default=None):
        return self._config.get(key, default)

    def set(self, key: str, value: Any):
        self._config[key] = value
        self.save()

    def update(self, new_data: Dict[str, Any]):
        self._config.update(new_data)
        self.save()

    def all(self) -> Dict[str, Any]:
        cfg = self._config.copy()
        cfg["METAL_PROFILES"] = METAL_PROFILES
        cfg["ANALYSIS_MODES"] = ANALYSIS_MODES
        return cfg

    def get_metal_profile(self, metal_key: str = None) -> Dict[str, Any]:
        key = metal_key or self.get("SELECTED_METAL", "carbon_steel")
        return METAL_PROFILES.get(key, METAL_PROFILES["carbon_steel"])

    def get_analysis_mode(self, mode_key: str = None) -> Dict[str, Any]:
        key = mode_key or self.get("ANALYSIS_TYPE", "standard")
        return ANALYSIS_MODES.get(key, ANALYSIS_MODES["standard"])

    def __getattr__(self, name: str):
        if name in self._config:
            return self._config[name]
        raise AttributeError(f"AppConfig has no attribute {name}")

# Global singleton
config = AppConfig()
