# Panduan Integrasi Database (`db_manager.py`)

File `db_manager.py` menyediakan fungsi-fungsi siap pakai untuk komunikasi antara AI Counting, Database, dan Dashboard.

---

## 1. Untuk Tim AI / Computer Vision (Orang 1)
Panggil fungsi `log_counting_event` setiap kali objek menyeberangi garis deteksi (*crossing line*).

```python
from db_manager import log_counting_event

# Contoh: 1 Orang Masuk di CCTV Channel 1
log_counting_event(cctv_channel=1, in_inc=1, out_inc=0)

# Contoh: 1 Orang Keluar di CCTV Channel 1
log_counting_event(cctv_channel=1, in_inc=0, out_inc=1)