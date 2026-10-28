from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Ganti 'PASSWORD_ANDA' dengan password saat Anda menginstal PostgreSQL
# 'driver_app_db' adalah nama database yang akan kita gunakan
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:gus1234@localhost:8000/driver_app_db"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Fungsi untuk membuka koneksi setiap kali ada request API
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()  