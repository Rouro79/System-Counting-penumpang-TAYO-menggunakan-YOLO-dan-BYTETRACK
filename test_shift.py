from db_manager import get_current_shift_id, start_new_session, get_active_session_info

def run_test():
    print("=== PENGUJIAN TAHAP 3: LOGIKA SHIFT & SESI OPERASIONAL ===")
    
    # 1. Cek Shift yang sedang aktif berdasarkan jam komputer saat ini
    current_shift = get_current_shift_id()
    print(f"[+] Shift ID saat ini (berdasarkan jam sistem): {current_shift}")
    
    # 2. Simulasi membuat Sesi Baru untuk CCTV Channel 1 (Bus TAYO-01, Supir Pak Budi)
    print("[+] Membuat sesi operasional baru untuk CCTV Channel 1...")
    start_new_session(bus_id=1, driver_id=1, cctv_channel=1)
    
    # 3. Ambil detail sesi aktif untuk memastikan data terhubung
    session_info = get_active_session_info(cctv_channel=1)
    
    if session_info:
        print("\n--- DETAIL SESI AKTIF CCTV 1 ---")
        print(f"ID Sesi        : {session_info['session_id']}")
        print(f"Kode Bus       : {session_info['bus_code']} ({session_info['plate_number']})")
        print(f"Nama Supir     : {session_info['driver_name']}")
        print(f"Nama Shift     : {session_info['shift_name']}")
        print(f"Channel CCTV   : {session_info['cctv_channel']}")
        print("--------------------------------")
        print(" Pengujian Tahap 3 Berhasil! Sistem Shift Siap Digunakan.")
    else:
        print("❌ Sesi aktif tidak ditemukan. Periksa kembali db_manager.py.")

if __name__ == "__main__":
    run_test()