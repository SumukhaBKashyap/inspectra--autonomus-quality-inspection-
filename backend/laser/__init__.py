from .laser_capture import capture_laser_frame
from .laser_profile import extract_laser_line_profile, build_reference_baseline
from .triangulation import compute_triangulation_height

def process_laser_inspection(
    is_defective: bool = False,
    metal_type: str = None,
    analysis_mode: str = None
) -> dict:
    """Convenience wrapper to run full laser inspection pipeline with material criteria."""
    frame = capture_laser_frame(is_defective=is_defective)
    centroids = extract_laser_line_profile(frame)
    baseline = build_reference_baseline(frame.shape[1], default_row=240.0)
    return compute_triangulation_height(
        centroids,
        baseline,
        metal_type=metal_type,
        analysis_mode=analysis_mode
    )
