"""
Inspectra - Central Quality Inspection and Sorting System Backend
FastAPI Main Application Entrypoint
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .config import config
from .database import init_db
from .api import inspection_router, hardware_router, settings_router, stream_router, handle_inspection_ws
from .hardware import arduino

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize database tables
    init_db()
    # Try connecting to Arduino if not in simulation mode
    if not config.HARDWARE_SIMULATION_MODE:
        try:
            await arduino.connect()
        except Exception as e:
            print(f"[Startup] Could not auto-connect to Arduino: {e}")
    yield
    # Shutdown: cleanly close serial
    await arduino.disconnect()

app = FastAPI(
    title="Inspectra Automated Quality Inspection System",
    description="Central control, 3-module inspection, and automated sorting engine",
    version="2.0.0",
    lifespan=lifespan
)

# Enable CORS for frontend dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount media folder for inspection image access
media_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "media")
os.makedirs(media_dir, exist_ok=True)
app.mount("/media", StaticFiles(directory=media_dir), name="media")

# Include modular API routers
app.include_router(inspection_router)
app.include_router(hardware_router)
app.include_router(settings_router)
app.include_router(stream_router)

# Real-time WebSocket endpoint
@app.websocket("/ws/inspection/{inspection_id}")
async def websocket_endpoint(websocket: WebSocket, inspection_id: str):
    await handle_inspection_ws(websocket, inspection_id)

@app.get("/health")
def health():
    return {
        "status": "online",
        "service": "Inspectra",
        "hardware_simulation": config.HARDWARE_SIMULATION_MODE,
        "eddy_method": "ARRAY_ECI",
        "cv_method": "REAL",
        "laser_method": "REAL"
    }

from fastapi.responses import FileResponse

# Mount production frontend build (serves React directly on port 8000)
dist_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend", "dist")
if os.path.exists(dist_dir):
    assets_dir = os.path.join(dist_dir, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        file_path = os.path.join(dist_dir, full_path)
        if full_path and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(dist_dir, "index.html"))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)

