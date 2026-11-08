"""CRUD and aggregation queries for Inspectra database."""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from . import models

def get_inspection(db: Session, inspection_id: str) -> Optional[models.Inspection]:
    return db.query(models.Inspection).filter(models.Inspection.id == inspection_id).first()

def list_inspections(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    outcome: Optional[str] = None,
    component_type: Optional[str] = None
) -> List[models.Inspection]:
    query = db.query(models.Inspection).outerjoin(models.Decision)
    if outcome:
        query = query.filter(models.Decision.outcome == outcome.upper())
    if component_type:
        query = query.filter(models.Decision.component_type == component_type.upper())
    return query.order_by(models.Inspection.created_at.desc()).offset(skip).limit(limit).all()

def get_statistics(db: Session) -> Dict[str, Any]:
    total = db.query(models.Inspection).count()
    if total == 0:
        return {
            "total": 0,
            "pass_count": 0,
            "fail_count": 0,
            "review_count": 0,
            "nut_count": 0,
            "washer_count": 0,
            "unknown_count": 0,
            "pass_rate_pct": 0.0,
            "fail_rate_pct": 0.0,
            "review_rate_pct": 0.0,
            "defects_by_type": {
                "cv_surface_defects": 0,
                "laser_height_anomalies": 0,
                "eddy_anomalies_simulated": 0
            }
        }

    pass_count = db.query(models.Decision).filter(models.Decision.outcome == "PASS").count()
    fail_count = db.query(models.Decision).filter(models.Decision.outcome == "FAIL").count()
    review_count = db.query(models.Decision).filter(models.Decision.outcome == "REVIEW").count()

    nut_count = db.query(models.Decision).filter(models.Decision.component_type == "NUT").count()
    washer_count = db.query(models.Decision).filter(models.Decision.component_type == "WASHER").count()
    unknown_count = db.query(models.Decision).filter(models.Decision.component_type == "UNKNOWN").count()

    # Defects breakdown
    cv_defect_count = db.query(models.CVResult).filter(models.CVResult.status != "PASS").count()
    laser_defect_count = db.query(models.LaserResult).filter(models.LaserResult.status != "PASS").count()
    eddy_defect_count = db.query(models.EddyResult).filter(models.EddyResult.status != "PASS").count()

    return {
        "total": total,
        "pass_count": pass_count,
        "fail_count": fail_count,
        "review_count": review_count,
        "nut_count": nut_count,
        "washer_count": washer_count,
        "unknown_count": unknown_count,
        "pass_rate_pct": round((pass_count / total) * 100, 1) if total else 0.0,
        "fail_rate_pct": round((fail_count / total) * 100, 1) if total else 0.0,
        "review_rate_pct": round((review_count / total) * 100, 1) if total else 0.0,
        "defects_by_type": {
            "cv_surface_defects": cv_defect_count,
            "laser_height_anomalies": laser_defect_count,
            "eddy_anomalies_simulated": eddy_defect_count
        }
    }

def delete_all_inspections(db: Session) -> int:
    count = db.query(models.Inspection).delete()
    db.commit()
    return count

