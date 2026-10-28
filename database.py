from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Ganti 'PASSWORD_ANDA' dengan password saat Anda menginstal PostgreSQL
# 'driver_app_db' adalah nama database yang akan kita gunakan
SQLALCHEMY_DATABASE_URL = "postgresql://neondb_owner:npg_IzWqsx3arB9b@ep-red-cherry-azcv8ya2.c-3.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

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
