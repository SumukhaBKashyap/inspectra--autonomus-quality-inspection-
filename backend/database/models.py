"""SQLAlchemy models for Inspectra Automated Quality Inspection."""

import datetime
from sqlalchemy import Column, String, Integer, Float, JSON, ForeignKey, DateTime, Boolean, Text
from sqlalchemy.orm import relationship
from .db import Base

class Inspection(Base):
    __tablename__ = "inspections"
    id = Column(String, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    status = Column(String, default="IN_PROGRESS") # IN_PROGRESS, COMPLETED, ERROR
    duration_ms = Column(Float, default=0.0)

    # Relationships
    images = relationship("Image", back_populates="inspection", cascade="all, delete-orphan")
    cv_result = relationship("CVResult", uselist=False, back_populates="inspection", cascade="all, delete-orphan")
    laser_result = relationship("LaserResult", uselist=False, back_populates="inspection", cascade="all, delete-orphan")
    eddy_result = relationship("EddyResult", uselist=False, back_populates="inspection", cascade="all, delete-orphan")
    decision = relationship("Decision", uselist=False, back_populates="inspection", cascade="all, delete-orphan")

class Image(Base):
    __tablename__ = "images"
    id = Column(Integer, primary_key=True, autoincrement=True)
    inspection_id = Column(String, ForeignKey("inspections.id"), nullable=False, index=True)
    label = Column(String, default="0deg") # 0deg, 90deg, laser
    path = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    inspection = relationship("Inspection", back_populates="images")

class CVResult(Base):
    __tablename__ = "cv_results"
    inspection_id = Column(String, ForeignKey("inspections.id"), primary_key=True)
    status = Column(String, default="PASS") # PASS, FAIL, REVIEW
    component_type = Column(String, default="unknown") # nut, washer, unknown
    confidence = Column(Float, default=0.0)
    circularity = Column(Float, default=0.0)
    corners_detected = Column(Integer, default=0)
    dimensions = Column(JSON) # {"outer_diameter_mm": 21.1, "inner_diameter_mm": 10.2, ...}
    tolerances = Column(JSON) # {"outer_status": "PASS", "inner_status": "PASS", ...}
    defects = Column(JSON) # list of defect descriptions
    multi_angle_match = Column(Boolean, default=True)
    inspection = relationship("Inspection", back_populates="cv_result")

class LaserResult(Base):
    __tablename__ = "laser_results"
    inspection_id = Column(String, ForeignKey("inspections.id"), primary_key=True)
    status = Column(String, default="PASS") # PASS, FAIL, REVIEW
    max_height_variation_mm = Column(Float, default=0.0)
    mean_height_mm = Column(Float, default=0.0)
    peak_height_mm = Column(Float, default=0.0)
    is_calibrated = Column(Boolean, default=True)
    profile_data = Column(JSON) # sampled 1D array of surface heights
    reference_data = Column(JSON) # expected baseline profile
    anomalies = Column(JSON) # list of profile anomalies
    inspection = relationship("Inspection", back_populates="laser_result")

class EddyResult(Base):
    __tablename__ = "eddy_results"
    inspection_id = Column(String, ForeignKey("inspections.id"), primary_key=True)
    status = Column(String, default="PASS") # PASS, FAIL, REVIEW
    is_simulated = Column(Boolean, default=True) # ALWAYS True - SIMULATED
    nominal_impedance = Column(Float, default=1.0)
    max_deviation_pct = Column(Float, default=0.0)
    simulated_readings = Column(JSON) # 8-12 coil readings around perimeter
    anomalies = Column(JSON) # list of detected anomalies
    inspection = relationship("Inspection", back_populates="eddy_result")

class Decision(Base):
    __tablename__ = "decisions"
    inspection_id = Column(String, ForeignKey("inspections.id"), primary_key=True)
    component_type = Column(String, default="UNKNOWN") # NUT, WASHER, UNKNOWN
    cv_status = Column(String, default="PASS")
    laser_status = Column(String, default="PASS")
    eddy_status = Column(String, default="PASS")
    outcome = Column(String, default="PASS") # PASS, FAIL, REVIEW
    reason = Column(Text, default="")
    sorting_command = Column(String, default="STOP_CONVEYOR") # SORT_NUT, SORT_WASHER, STOP_CONVEYOR
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    inspection = relationship("Inspection", back_populates="decision")

class HardwareLog(Base):
    __tablename__ = "hardware_logs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    command = Column(String, nullable=False)
    payload = Column(JSON, nullable=True)
    response = Column(String, nullable=True)
    duration_ms = Column(Float, default=0.0)
    success = Column(Boolean, default=True)

