import time
from db_manager import log_counting_event, get_live_stats, get_active_session_info

def run_integration_test():
    print("=== PENGUJIAN TAHAP 4: SIMULASI ALUR AI -> DATABASE -> DASHBOARD ===")
    
    cctv_channel = 1
    
    # 1. Ambil Informasi Sesi Aktif (Untuk Dashboard)
    session = get_active_session_info(cctv_channel)
    if session:
        print(f"[Dashboard] Terhubung ke Bus: {session['bus_code']} | Driver: {session['driver_name']}")
    else:
        print("❌ Sesi aktif tidak ditemukan!")
        return

    # 2. Simulasi AI Mengirim Data Deteksi Penumpang (Orang 1)
    print("\n[AI Module] Memulai simulasi perhitungan penumpang...")
    print("[AI Module] Deteksi: 1 Orang Masuk di CCTV 1")
    log_counting_event(cctv_channel=cctv_channel, in_inc=1, out_inc=0)
    time.sleep(1)

    print("[AI Module] Deteksi: 2 Orang Masuk, 1 Orang Keluar di CCTV 1")
    log_counting_event(cctv_channel=cctv_channel, in_inc=2, out_inc=1)
    time.sleep(1)

    # 3. Simulasi Dashboard Mengambil Data Real-Time (Orang 4)
    print("\n[Dashboard] Membaca total rekapitulasi data dari Database...")
    stats = get_live_stats()
    
    print("\n--- REKAPITULASI LIVE DASHBOARD ---")
    for stat in stats:
        if stat['cctv_channel'] == cctv_channel:
            total_in = stat['total_in']
            total_out = stat['total_out']
            penumpang_di_bus = total_in - total_out
            print(f"CCTV Channel : {stat['cctv_channel']}")
            print(f"Total Masuk  : {total_in} orang")
            print(f"Total Keluar : {total_out} orang")
            print(f"Total Penumpang: {total_in} orang")
            print(f"Penumpang Saat Ini (Di Dalam Bus): {penumpang_di_bus} orang")
    print("------------------------------------")
    print(" SELAMAT! Integrasi Database Berhasil 100%.")

if __name__ == "__main__":
    run_integration_test()