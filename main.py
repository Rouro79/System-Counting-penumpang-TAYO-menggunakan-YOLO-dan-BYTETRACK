from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
import models, schemas
from database import engine, get_db
from sqlalchemy.sql import func

# Otomatis membuat tabel di PostgreSQL
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="API Aplikasi Supir")

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Mengizinkan semua domain website mengakses API
    allow_credentials=True,
    allow_methods=["*"], # Mengizinkan semua metode (GET, POST, PUT, DELETE)
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"pesan": "Server API Aplikasi Supir Berjalan!"}

# 1. API Tambah Supir Baru
@app.post("/api/v1/drivers")
def create_driver(driver: schemas.DriverCreate, db: Session = Depends(get_db)):
    new_driver = models.Driver(
        name=driver.name, 
        phone_number=driver.phone_number, 
        license_number=driver.license_number
    )
    db.add(new_driver)
    db.commit()
    db.refresh(new_driver)
    return {"status": "sukses", "data": new_driver}

# 2. API Mulai Shift (Supir Mulai Jalan)
@app.post("/api/v1/shifts/start")
def start_shift(shift: schemas.ShiftStart, db: Session = Depends(get_db)):
    # Pastikan supir ada di database
    driver_check = db.query(models.Driver).filter(models.Driver.id == shift.driver_id).first()
    if not driver_check:
        raise HTTPException(status_code=404, detail="Supir tidak ditemukan!")

    new_shift = models.Shift(
        driver_id=shift.driver_id, 
        bus_id=shift.bus_id, 
        route_name=shift.route_name
    )
    db.add(new_shift)
    db.commit()
    db.refresh(new_shift)
    return {"status": "sukses", "pesan": "Perjalanan dimulai", "shift_id": new_shift.id}

# 3. API Selesai Shift (Supir Selesai Jalan)
@app.put("/api/v1/shifts/end/{shift_id}")
def end_shift(shift_id: int, db: Session = Depends(get_db)):
    shift = db.query(models.Shift).filter(models.Shift.id == shift_id).first()
    if not shift:
        raise HTTPException(status_code=404, detail="Shift tidak ditemukan!")
    
    shift.end_time = func.now()
    db.commit()
    return {"status": "sukses", "pesan": "Perjalanan selesai dicatat"}

# 4. API Lapor Insiden (Mogok/Kecelakaan/Macet)
@app.post("/api/v1/incidents")
def report_incident(incident: schemas.IncidentCreate, db: Session = Depends(get_db)):
    new_incident = models.IncidentReport(
        shift_id=incident.shift_id,
        incident_type=incident.incident_type,
        description=incident.description
    )
    db.add(new_incident)
    db.commit()
    return {"status": "sukses", "pesan": f"Laporan {incident.incident_type} berhasil dikirim"}

# 5. API Dashboard: Pantau Supir Aktif (Sedang di jalan)
@app.get("/api/v1/dashboard/active-shifts")
def get_active_shifts(db: Session = Depends(get_db)):
    # Mencari shift yang waktu selesainya (end_time) masih kosong
    active_shifts = db.query(models.Shift).filter(models.Shift.end_time == None).all()
    return {
        "status": "sukses", 
        "total_supir_aktif": len(active_shifts), 
        "data": active_shifts
    }

# 6. API Dashboard: Riwayat Laporan Insiden
@app.get("/api/v1/dashboard/incidents")
def get_all_incidents(db: Session = Depends(get_db)):
    # Mengambil semua laporan, diurutkan dari yang paling baru
    incidents = db.query(models.IncidentReport).order_by(models.IncidentReport.timestamp.desc()).all()
    return {
        "status": "sukses", 
        "total_laporan": len(incidents),
        "data": incidents
    }