"""SQLAlchemy models for Inspectra.
Defines tables for inspections, images, and module results.
"""

from sqlalchemy import Column, String, Integer, Float, JSON, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from .database import Base
import datetime

class Inspection(Base):
    __tablename__ = "inspections"
    id = Column(String, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    # relationships
    images = relationship("Image", back_populates="inspection", cascade="all, delete-orphan")
    cv_result = relationship("CVResult", uselist=False, back_populates="inspection")
    laser_result = relationship("LaserResult", uselist=False, back_populates="inspection")
    eddy_result = relationship("EddyResult", uselist=False, back_populates="inspection")
    decision = relationship("Decision", uselist=False, back_populates="inspection")

class Image(Base):
    __tablename__ = "images"
    id = Column(Integer, primary_key=True, autoincrement=True)
    inspection_id = Column(String, ForeignKey("inspections.id"), nullable=False)
    path = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    inspection = relationship("Inspection", back_populates="images")

class CVResult(Base):
    __tablename__ = "cv_results"
    inspection_id = Column(String, ForeignKey("inspections.id"), primary_key=True)
    component_type = Column(String)  # "nut" or "washer" or "unknown"
    dimensions = Column(JSON)  # e.g. {"diameter": 12.3, "thickness": 4.1}
    defects = Column(JSON)  # list of detected defect strings
    inspection = relationship("Inspection", back_populates="cv_result")

class LaserResult(Base):
    __tablename__ = "laser_results"
    inspection_id = Column(String, ForeignKey("inspections.id"), primary_key=True)
    height_map = Column(JSON)  # placeholder for surface profile data
    anomalies = Column(JSON)  # list of detected anomalies
    inspection = relationship("Inspection", back_populates="laser_result")

class EddyResult(Base):
    __tablename__ = "eddy_results"
    inspection_id = Column(String, ForeignKey("inspections.id"), primary_key=True)
    simulated_readings = Column(JSON)  # raw coil values
    anomalies = Column(JSON)  # list of detected anomalies (simulated)
    inspection = relationship("Inspection", back_populates="eddy_result")

class Decision(Base):
    __tablename__ = "decisions"
    inspection_id = Column(String, ForeignKey("inspections.id"), primary_key=True)
    outcome = Column(String)  # PASS, FAIL, REVIEW, UNKNOWN
    reason = Column(String)  # human‑readable explanation
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    inspection = relationship("Inspection", back_populates="decision")
