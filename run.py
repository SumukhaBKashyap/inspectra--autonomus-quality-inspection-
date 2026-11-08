"""
Inspectra - Quick Launcher
Starts the Inspectra FastAPI application on http://localhost:8000
"""

import sys
import os
import uvicorn

if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)

