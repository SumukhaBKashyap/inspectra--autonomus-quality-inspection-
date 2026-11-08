'''FastAPI application for Inspectra automated quality inspection and sorting workflow'''

import uuid
import asyncio
import os
from fastapi import FastAPI, WebSocket, UploadFile, File, Depends, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy.orm import Session
from . import database, models, cv, laser, eddy, decision

DEMO_MODE = os.getenv("INSPECTRA_DEMO", "true").lower() == "true"

app = FastAPI(title="Inspectra Inspection Service", version="1.0.0")

# Initialize DB on startup
@app.on_event("startup")
async def startup_event():
    database.init_db()

# Allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to get DB session
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

class StartInspectionRequest(BaseModel):
    pass

@app.get("/health")
async def health():
    return {"status": "ok", "demo_mode": DEMO_MODE}

@app.get("/inspections")
async def list_inspections(db: Session = Depends(get_db)):
    """List all past inspections with their decisions."""
    rows = db.query(models.Inspection).order_by(models.Inspection.created_at.desc()).limit(50).all()
    result = []
    for insp in rows:
        d = insp.decision
        result.append({
            "id": insp.id,
            "created_at": insp.created_at.isoformat() if insp.created_at else None,
            "outcome": d.outcome if d else None,
            "reason": d.reason if d else None,
        })
    return result

@app.get("/inspections/{inspection_id}")
async def get_inspection(inspection_id: str, db: Session = Depends(get_db)):
    """Return full details for a single inspection."""
    insp = db.query(models.Inspection).filter(models.Inspection.id == inspection_id).first()
    if not insp:
        raise HTTPException(status_code=404, detail="Inspection not found")
    return {
        "id": insp.id,
        "created_at": insp.created_at.isoformat() if insp.created_at else None,
        "cv_result": {
            "component_type": insp.cv_result.component_type,
            "dimensions": insp.cv_result.dimensions,
            "defects": insp.cv_result.defects,
        } if insp.cv_result else None,
        "laser_result": {
            "height_map": insp.laser_result.height_map,
            "anomalies": insp.laser_result.anomalies,
        } if insp.laser_result else None,
        "eddy_result": {
            "simulated_readings": insp.eddy_result.simulated_readings,
            "anomalies": insp.eddy_result.anomalies,
        } if insp.eddy_result else None,
        "decision": {
            "outcome": insp.decision.outcome,
            "reason": insp.decision.reason,
            "created_at": insp.decision.created_at.isoformat() if insp.decision and insp.decision.created_at else None,
        } if insp.decision else None,
    }

@app.post("/inspection/start")
async def start_inspection(request: StartInspectionRequest, db: Session = Depends(get_db)):
    """Kick-off a new inspection sequence."""
    inspection_id = str(uuid.uuid4())
    db_inspection = models.Inspection(id=inspection_id)
    db.add(db_inspection)
    db.commit()
    asyncio.create_task(run_pipeline(inspection_id))
    return JSONResponse(content={"inspection_id": inspection_id})

@app.websocket("/ws/inspection/{inspection_id}")
async def inspection_ws(websocket: WebSocket, inspection_id: str):
    await websocket.accept()
    queue = decision.get_update_queue(inspection_id)
    try:
        while True:
            update = await asyncio.wait_for(queue.get(), timeout=60.0)
            await websocket.send_json(update)
            if update.get("type") == "complete":
                break
    except (asyncio.TimeoutError, Exception):
        pass
    finally:
        await websocket.close()

@app.post("/inspection/{inspection_id}/upload_image")
async def upload_image(inspection_id: str, file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Receive an image captured on the Android device."""
    media_dir = os.path.join(os.getcwd(), "media", inspection_id)
    os.makedirs(media_dir, exist_ok=True)
    file_path = os.path.join(media_dir, file.filename)
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    img = models.Image(inspection_id=inspection_id, path=file_path)
    db.add(img)
    db.commit()
    return {"filename": file.filename}

# ---------------------------------------------------------------------------
# Demo hardware stubs
# ---------------------------------------------------------------------------
async def _demo_conveyor_start():
    await asyncio.sleep(0.5)

async def _demo_wait_arrival():
    await asyncio.sleep(1.0)

async def _demo_transfer():
    await asyncio.sleep(0.5)

async def _demo_sorting(outcome, component_type):
    await asyncio.sleep(0.5)

# ---------------------------------------------------------------------------
# Core pipeline
# ---------------------------------------------------------------------------
async def run_pipeline(inspection_id: str):
    """Orchestrates the entire inspection workflow."""
    db = database.SessionLocal()
    try:
        # Stage 1
        await decision.report_progress(inspection_id, "stage", "feeding started")
        if DEMO_MODE:
            await _demo_conveyor_start()
            await _demo_wait_arrival()
            await _demo_transfer()
        else:
            from . import hardware
            await hardware.start_conveyor_1()
            await hardware.wait_for_component_arrival()
            await hardware.transfer_to_platform()
        await decision.report_progress(inspection_id, "stage", "feeding completed")

        # Stage 2 – CV
        await decision.report_progress(inspection_id, "module", "cv started")
        cv_result = cv.analyze_images([])  # demo: no real images
        db_cv = models.CVResult(
            inspection_id=inspection_id,
            component_type=cv_result["component_type"],
            dimensions=cv_result["dimensions"],
            defects=cv_result["defects"],
        )
        db.add(db_cv)
        db.commit()
        await decision.report_progress(inspection_id, "module", "cv completed")

        # Stage 2 – Laser
        await decision.report_progress(inspection_id, "module", "laser started")
        laser_result = laser.process_profile(inspection_id)
        db_laser = models.LaserResult(
            inspection_id=inspection_id,
            height_map=laser_result["height_map"],
            anomalies=laser_result["anomalies"],
        )
        db.add(db_laser)
        db.commit()
        await decision.report_progress(inspection_id, "module", "laser completed")

        # Stage 2 – Eddy
        await decision.report_progress(inspection_id, "module", "eddy started")
        eddy_result = eddy.simulate_readings()
        db_eddy = models.EddyResult(
            inspection_id=inspection_id,
            simulated_readings=eddy_result["simulated_readings"],
            anomalies=eddy_result["anomalies"],
        )
        db.add(db_eddy)
        db.commit()
        await decision.report_progress(inspection_id, "module", "eddy completed")

        # Decision
        await decision.report_progress(inspection_id, "stage", "decision engine")
        decision_data = decision.evaluate(cv=cv_result, laser=laser_result, eddy=eddy_result)
        reason_text = decision_data.get("reasons_text", "")
        db_decision = models.Decision(
            inspection_id=inspection_id,
            outcome=decision_data["outcome"],
            reason=reason_text,
        )
        db.add(db_decision)
        db.commit()
        await decision.report_progress(inspection_id, "decision", decision_data["outcome"])

        # Stage 3 – Sorting
        await decision.report_progress(inspection_id, "stage", "sorting started")
        if DEMO_MODE:
            await _demo_sorting(decision_data["outcome"], cv_result.get("component_type"))
        else:
            from . import hardware
            await hardware.execute_sorting(decision_data["outcome"], cv_result.get("component_type"))
        await decision.report_progress(inspection_id, "stage", "sorting completed")

        await decision.report_progress(inspection_id, "complete", "inspection finished")
        decision.close_queue(inspection_id)
    except Exception as e:
        await decision.report_progress(inspection_id, "error", str(e))
        decision.close_queue(inspection_id)
    finally:
        db.close()
