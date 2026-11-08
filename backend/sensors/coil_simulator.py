"""
Inspectra - Eddy Current Array Inspection Module
Performs high-frequency multi-coil eddy current analysis tailored to the
active conveyor metal alloy and inspection criteria.
Calculates coil impedance, phase angle, probe lift-off distance, and SNR.
"""

import random
import math
from typing import Dict, Any, List, Optional
from ..config import config

def simulate_eddy_current_scan(
    force_defect: bool = False,
    defect_coil_index: Optional[int] = None,
    metal_type: Optional[str] = None,
    analysis_mode: Optional[str] = None,
    seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    Execute 8-coil perimeter eddy current inspection array.
    Analyzes impedance response and phase signature against metal alloy baseline.
    """
    rng = random.Random(seed)
    metal = config.get_metal_profile(metal_type)
    mode = config.get_analysis_mode(analysis_mode)

    nominal_z = float(metal["eddy_nominal_impedance"])
    base_phase = float(metal["eddy_phase_deg"])
    freq_khz = int(metal["eddy_frequency_khz"])
    
    # Calculate effective threshold from metal profile and analysis mode multiplier
    base_tol_pct = float(metal["eddy_tolerance_pct"])
    effective_tol_pct = round(base_tol_pct * float(mode["eddy_tolerance_multiplier"]), 1)
    threshold_fraction = effective_tol_pct / 100.0

    num_coils = 8
    readings: List[Dict[str, Any]] = []
    anomalies: List[str] = []

    has_defect = force_defect
    chosen_defect_idx = defect_coil_index if defect_coil_index is not None else rng.randint(0, num_coils - 1)

    max_deviation = 0.0

    for i in range(num_coils):
        angle_deg = i * (360 // num_coils)
        
        # Microscopic lift-off fluctuation (120 ± 8 μm)
        lift_off_um = round(120.0 + rng.gauss(0, 4.5), 1)

        # Baseline thermal and grain noise (typically ±2% of nominal)
        noise = rng.gauss(0, 0.018) * nominal_z
        phase_noise = rng.gauss(0, 0.8)

        # Defect signature injection
        defect_spike = 0.0
        phase_shift = 0.0
        if has_defect and (i == chosen_defect_idx):
            # Significant crack/void impedance spike and phase distortion
            defect_spike = rng.uniform(threshold_fraction * 1.35, threshold_fraction * 2.6) * nominal_z * rng.choice([-1.0, 1.0])
            phase_shift = rng.uniform(9.0, 18.0) * rng.choice([-1.0, 1.0])

        measured_z = round(nominal_z + noise + defect_spike, 3)
        measured_phase = round(base_phase + phase_noise + phase_shift, 1)

        deviation_ratio = abs(measured_z - nominal_z) / nominal_z
        dev_pct = round(deviation_ratio * 100.0, 2)
        if dev_pct > max_deviation:
            max_deviation = dev_pct

        # Realistic Signal-to-Noise Ratio (dB)
        snr_db = round(38.0 + rng.uniform(-1.5, 3.5) - (6.0 if has_defect and i == chosen_defect_idx else 0.0), 1)

        is_coil_anomaly = deviation_ratio > threshold_fraction

        reading = {
            "coil_index": i,
            "angle_deg": angle_deg,
            "impedance": measured_z,
            "nominal_impedance": nominal_z,
            "phase_angle_deg": measured_phase,
            "lift_off_um": lift_off_um,
            "snr_db": snr_db,
            "deviation_pct": dev_pct,
            "is_anomaly": is_coil_anomaly,
            "status": "ANOMALY" if is_coil_anomaly else "NORMAL"
        }
        readings.append(reading)

        if is_coil_anomaly:
            anomalies.append(
                f"ECI Coil #{i} ({angle_deg}°): impedance {measured_z} Ω (dev {dev_pct}%) exceeds {effective_tol_pct}% limit — subsurface flaw/void indication"
            )

    status = "FAIL" if len(anomalies) > 0 else "PASS"

    summary = (
        f"Eddy Current Scan ({metal['short_name']}): 8 coils @ {freq_khz} kHz. "
        f"{'Passed: all coils within tolerance envelope.' if status == 'PASS' else f'{len(anomalies)} anomaly(ies) detected.'}"
    )

    return {
        "status": status,
        "metal_name": metal["name"],
        "category": metal["category"],
        "frequency_khz": freq_khz,
        "operating_freq_khz": freq_khz,
        "nominal_impedance": nominal_z,
        "base_phase_deg": base_phase,
        "snr_db": round(sum(r["snr_db"] for r in readings) / len(readings), 1),
        "lift_off_um": lift_off_um,
        "max_deviation_pct": round(max_deviation, 2),
        "threshold_pct": effective_tol_pct,
        "readings": readings,
        "anomalies": anomalies,
        "summary": summary
    }
