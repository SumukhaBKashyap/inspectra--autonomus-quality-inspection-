"""Inspectra backend package.
Provides FastAPI entry‑point and utility sub‑modules.
"""

# Export commonly used symbols for convenient import
from . import database, models, hardware, cv, laser, eddy, decision
