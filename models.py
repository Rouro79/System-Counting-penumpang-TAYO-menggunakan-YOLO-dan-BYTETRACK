from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from database import Base

class Driver(Base):
    __tablename__ = "drivers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    phone_number = Column(String, unique=True)
    license_number = Column(String, unique=True) # Nomor SIM

class Bus(Base):
    __tablename__ = "buses"
    id = Column(Integer, primary_key=True, index=True)
    plate_number = Column(String, unique=True, index=True)
    condition_status = Column(String, default="Baik") # Baik, Rusak, Perawatan

class Shift(Base):
    __tablename__ = "shifts"
    id = Column(Integer, primary_key=True, index=True)
    driver_id = Column(Integer, ForeignKey("drivers.id"))
    bus_id = Column(Integer, ForeignKey("buses.id"))
    route_name = Column(String) # Misal: Blok M - Kota
    start_time = Column(DateTime(timezone=True), server_default=func.now())
    end_time = Column(DateTime(timezone=True), nullable=True)

class IncidentReport(Base):
    __tablename__ = "incident_reports"
    id = Column(Integer, primary_key=True, index=True)
    shift_id = Column(Integer, ForeignKey("shifts.id"))
    incident_type = Column(String) # Kecelakaan, Mogok, Macet Total
    description = Column(Text)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())