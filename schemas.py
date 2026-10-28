from pydantic import BaseModel
from typing import Optional

class DriverCreate(BaseModel):
    name: str
    phone_number: str
    license_number: str

class BusCreate(BaseModel):
    plate_number: str
    condition_status: str = "Baik"

class ShiftStart(BaseModel):
    driver_id: int
    bus_id: int
    route_name: str

class IncidentCreate(BaseModel):
    shift_id: int
    incident_type: str
    description: str