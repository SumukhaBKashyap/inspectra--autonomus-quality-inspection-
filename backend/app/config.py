"""
Inspectra – Configurable thresholds and settings.
All inspection decision thresholds live here so they can be tuned
without touching module logic.
"""

import os

# ---------------------------------------------------------------------------
# Serial / Hardware
# ---------------------------------------------------------------------------
SERIAL_PORT  = os.getenv("INSPECTRA_SERIAL_PORT", "COM3")
BAUD_RATE    = int(os.getenv("INSPECTRA_BAUD_RATE", "115200"))
SERIAL_TIMEOUT = float(os.getenv("INSPECTRA_SERIAL_TIMEOUT", "2.0"))

# How long to wait for a component to arrive on conveyor (seconds)
ARRIVAL_TIMEOUT   = float(os.getenv("INSPECTRA_ARRIVAL_TIMEOUT", "30.0"))
# How long to wait for a servo ACK (seconds)
SERVO_ACK_TIMEOUT = float(os.getenv("INSPECTRA_SERVO_ACK_TIMEOUT", "10.0"))

# ---------------------------------------------------------------------------
# Computer Vision thresholds
# ---------------------------------------------------------------------------
# Minimum contour area (px²) to be considered a component, not noise
CV_MIN_CONTOUR_AREA = int(os.getenv("CV_MIN_CONTOUR_AREA", "500"))

# Circularity threshold: ratio of 4π·area / perimeter²
# > 0.75 → round (washer);  ≤ 0.75 → polygonal (nut)
CV_CIRCULARITY_THRESHOLD = float(os.getenv("CV_CIRCULARITY_THRESHOLD", "0.75"))

# Minimum number of corners detected before classifying as nut
CV_NUT_MIN_CORNERS = int(os.getenv("CV_NUT_MIN_CORNERS", "5"))

# Calibration: mm per pixel (apply after camera calibration)
CV_MM_PER_PIXEL = float(os.getenv("CV_MM_PER_PIXEL", "0.1"))

# Maximum fraction of component area that may be defective
CV_MAX_DEFECT_FRACTION = float(os.getenv("CV_MAX_DEFECT_FRACTION", "0.05"))

# ---------------------------------------------------------------------------
# Laser thresholds
# ---------------------------------------------------------------------------
# Maximum allowed peak-to-valley height variation (mm) before flagging anomaly
LASER_MAX_HEIGHT_VARIATION_MM = float(os.getenv("LASER_MAX_HEIGHT_VARIATION_MM", "0.5"))

# Fraction of profile points allowed to deviate > 2σ before flagging
LASER_ANOMALY_FRACTION_THRESHOLD = float(os.getenv("LASER_ANOMALY_FRACTION_THRESHOLD", "0.10"))

# ---------------------------------------------------------------------------
# Eddy current thresholds  (readings are SIMULATED)
# ---------------------------------------------------------------------------
# Reading outside ± this fraction of nominal triggers an anomaly
EDDY_ANOMALY_THRESHOLD = float(os.getenv("EDDY_ANOMALY_THRESHOLD", "0.15"))

# Nominal impedance value for simulation baseline
EDDY_NOMINAL_IMPEDANCE = float(os.getenv("EDDY_NOMINAL_IMPEDANCE", "1.0"))

# ---------------------------------------------------------------------------
# Decision engine weights
# ---------------------------------------------------------------------------
# FAIL if any of these individual conditions are True
# (kept as a plain mapping so they can be extended without code changes)
DECISION_FAIL_ON_CV_DEFECTS   = os.getenv("DECISION_FAIL_ON_CV_DEFECTS",   "true").lower() == "true"
DECISION_FAIL_ON_LASER_ANOMALY = os.getenv("DECISION_FAIL_ON_LASER_ANOMALY", "true").lower() == "true"
DECISION_FAIL_ON_EDDY_ANOMALY  = os.getenv("DECISION_FAIL_ON_EDDY_ANOMALY",  "true").lower() == "true"

# If component_type is unknown, go to REVIEW (not outright FAIL)
DECISION_REVIEW_ON_UNKNOWN_TYPE = os.getenv("DECISION_REVIEW_ON_UNKNOWN_TYPE", "true").lower() == "true"
