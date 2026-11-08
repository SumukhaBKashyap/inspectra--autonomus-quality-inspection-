"""
Inspectra - Inspection API Endpoints
Handles inspection triggering, history queries, individual inspection details,
statistics aggregation, and CSV/JSON export.
"""

import os
import io
import csv
import json
import uuid
import asyncio
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db, models, crud
from ..inspection import inspection_manager

router = APIRouter(prefix="/api", tags=["inspection"])

class StartInspectionRequest(BaseModel):
    force_type: Optional[str] = None # "nut" or "washer" or None
    force_defect: bool = False
    metal_type: Optional[str] = None
    analysis_mode: Optional[str] = None

@router.post("/inspection/start")
async def start_inspection(req: StartInspectionRequest):
    """Trigger the 18-step automated inspection sequence."""
    inspection_id = str(uuid.uuid4())
    asyncio.create_task(
        inspection_manager.run_inspection_sequence(
            inspection_id=inspection_id,
            force_type=req.force_type,
            force_defect=req.force_defect,
            metal_type=req.metal_type,
            analysis_mode=req.analysis_mode
        )
    )
    return {"inspection_id": inspection_id, "status": "STARTED"}

class AutoInspectionRequest(BaseModel):
    metal_type: Optional[str] = None
    analysis_mode: Optional[str] = None

@router.post("/inspection/auto/start")
async def start_auto_inspection(req: AutoInspectionRequest):
    """Enable continuous sensor-driven autonomous inspection loop."""
    return await inspection_manager.start_auto_mode(
        metal_type=req.metal_type,
        analysis_mode=req.analysis_mode
    )

@router.post("/inspection/auto/stop")
async def stop_auto_inspection():
    """Halt continuous autonomous loop."""
    return await inspection_manager.stop_auto_mode()

@router.get("/inspection/auto/status")
def get_auto_inspection_status():
    """Check whether continuous autonomous loop is active."""
    return {
        "auto_mode": inspection_manager.is_auto_mode,
        "is_inspecting": inspection_manager.is_running
    }

@router.get("/inspections/stats")
def get_dashboard_stats(db: Session = Depends(get_db)):
    """Fetch aggregated statistics for the industrial dashboard."""
    return crud.get_statistics(db)

@router.get("/inspections")
def list_inspections(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    outcome: Optional[str] = None,
    component_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List inspection records with optional filtering."""
    records = crud.list_inspections(
        db,
        skip=skip,
        limit=limit,
        outcome=outcome,
        component_type=component_type
    )
    results = []
    for insp in records:
        dec = insp.decision
        cv = insp.cv_result
        results.append({
            "id": insp.id,
            "created_at": insp.created_at.isoformat() if insp.created_at else None,
            "status": insp.status,
            "duration_ms": round(insp.duration_ms, 1) if insp.duration_ms else 0,
            "outcome": dec.outcome if dec else "UNKNOWN",
            "component_type": dec.component_type if dec else "UNKNOWN",
            "cv_status": dec.cv_status if dec else "UNKNOWN",
            "laser_status": dec.laser_status if dec else "UNKNOWN",
            "eddy_status": dec.eddy_status if dec else "UNKNOWN",
            "reason": dec.reason if dec else "",
            "sorting_command": dec.sorting_command if dec else "STOP_CONVEYOR",
            "defects_count": len(cv.defects) if (cv and cv.defects) else 0,
            "dimensions": cv.dimensions if (cv and cv.dimensions) else {}
        })
    return results

@router.get("/inspections/{inspection_id}")
def get_inspection_details(inspection_id: str, db: Session = Depends(get_db)):
    """Fetch complete telemetry, images, and results for a single inspection."""
    insp = crud.get_inspection(db, inspection_id)
    if not insp:
        raise HTTPException(status_code=404, detail="Inspection not found")

    images_data = []
    for img in insp.images:
        images_data.append({
            "id": img.id,
            "label": img.label,
            "filename": os.path.basename(img.path),
            "url": f"/media/{insp.id}/{os.path.basename(img.path)}",
            "timestamp": img.timestamp.isoformat() if img.timestamp else None
        })

    return {
        "id": insp.id,
        "created_at": insp.created_at.isoformat() if insp.created_at else None,
        "status": insp.status,
        "duration_ms": insp.duration_ms,
        "images": images_data,
        "cv_result": {
            "status": insp.cv_result.status,
            "component_type": insp.cv_result.component_type,
            "confidence": insp.cv_result.confidence,
            "circularity": insp.cv_result.circularity,
            "corners_detected": insp.cv_result.corners_detected,
            "dimensions": insp.cv_result.dimensions,
            "tolerances": insp.cv_result.tolerances,
            "defects": insp.cv_result.defects,
            "multi_angle_match": insp.cv_result.multi_angle_match
        } if insp.cv_result else None,
        "laser_result": {
            "status": insp.laser_result.status,
            "max_height_variation_mm": insp.laser_result.max_height_variation_mm,
            "mean_height_mm": insp.laser_result.mean_height_mm,
            "peak_height_mm": insp.laser_result.peak_height_mm,
            "is_calibrated": insp.laser_result.is_calibrated,
            "profile_data": insp.laser_result.profile_data,
            "anomalies": insp.laser_result.anomalies
        } if insp.laser_result else None,
        "eddy_result": {
            "status": insp.eddy_result.status,
            "is_simulated": False,
            "nominal_impedance": insp.eddy_result.nominal_impedance,
            "max_deviation_pct": insp.eddy_result.max_deviation_pct,
            "simulated_readings": insp.eddy_result.simulated_readings,
            "anomalies": insp.eddy_result.anomalies
        } if insp.eddy_result else None,
        "decision": {
            "outcome": insp.decision.outcome,
            "component_type": insp.decision.component_type,
            "cv_status": insp.decision.cv_status,
            "laser_status": insp.decision.laser_status,
            "eddy_status": insp.decision.eddy_status,
            "reason": insp.decision.reason,
            "sorting_command": insp.decision.sorting_command,
            "created_at": insp.decision.created_at.isoformat() if insp.decision and insp.decision.created_at else None
        } if insp.decision else None
    }

@router.delete("/inspections")
def clear_all_inspections(db: Session = Depends(get_db)):
    """Clear all historical inspections."""
    count = crud.delete_all_inspections(db)
    return {"status": "cleared", "count": count}

@router.get("/inspections/export/csv")
def export_csv(db: Session = Depends(get_db)):
    """Export all inspections as a downloadable CSV report."""
    inspections = crud.list_inspections(db, skip=0, limit=1000)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Inspection ID", "Timestamp", "Outcome", "Component Type",
        "CV Status", "Laser Status", "Eddy Status",
        "Sorting Command", "Duration (ms)", "Reason"
    ])
    for insp in inspections:
        d = insp.decision
        writer.writerow([
            insp.id,
            insp.created_at.isoformat() if insp.created_at else "",
            d.outcome if d else "UNKNOWN",
            d.component_type if d else "UNKNOWN",
            d.cv_status if d else "",
            d.laser_status if d else "",
            d.eddy_status if d else "",
            d.sorting_command if d else "",
            f"{insp.duration_ms:.1f}",
            d.reason if d else ""
        ])
    output.seek(0)
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=inspectra_report.csv"}
    )

