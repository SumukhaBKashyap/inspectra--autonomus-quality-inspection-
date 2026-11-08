"""
Inspectra – Eddy Current Inspection Module (SIMULATED).

⚠️  ALL readings produced by this module are SIMULATED.
    No real eddy current hardware is connected.
    Results are clearly labelled SIMULATED throughout.
"""

from __future__ import annotations

import random
import math
from typing import Dict, Any, List

from . import config


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def simulate_readings(seed: int | None = None) -> Dict[str, Any]:
    """
    Generate simulated coil impedance readings and detect anomalies.

    Returns
    -------
    dict with keys:
        simulated_readings : list[dict]  – per-coil readings (SIMULATED)
        anomalies          : list[str]   – detected anomalies (SIMULATED)
        is_simulated       : True        – always True, for UI labelling
        summary            : str         – human-readable summary
    """
    rng = random.Random(seed)

    nominal = config.EDDY_NOMINAL_IMPEDANCE
    threshold = config.EDDY_ANOMALY_THRESHOLD

    # Simulate 8 coil positions around the component
    num_coils = 8
    readings: List[Dict[str, Any]] = []
    anomalies: List[str] = []

    for i in range(num_coils):
        angle_deg = i * (360 / num_coils)
        # Small random noise ±5 % of nominal under normal conditions
        noise = rng.gauss(0, 0.03) * nominal
        # Occasionally inject a larger defect signal (10 % chance per coil)
        defect_spike = 0.0
        if rng.random() < 0.10:
            defect_spike = rng.uniform(threshold, threshold * 2.5) * nominal * rng.choice([-1, 1])

        measured = nominal + noise + defect_spike
        deviation = abs(measured - nominal) / nominal

        reading = {
            "coil_index":    i,
            "angle_deg":     angle_deg,
            "impedance":     round(measured, 4),
            "deviation_pct": round(deviation * 100, 2),
            "simulated":     True,          # explicit per-reading flag
        }
        readings.append(reading)

        if deviation > threshold:
            anomalies.append(
                f"[SIMULATED] Coil {i} @ {angle_deg}°: impedance deviation "
                f"{deviation*100:.1f}% exceeds threshold {threshold*100:.0f}%"
            )

    summary = (
        f"[SIMULATED] Eddy current scan: {num_coils} coils measured. "
        f"{len(anomalies)} anomaly(ies) detected."
    )

    return {
        "simulated_readings": readings,
        "anomalies":          anomalies,
        "is_simulated":       True,
        "summary":            summary,
    }
