# UTS Sistem Terdistribusi: Event Aggregator Service

**Nama:** Dewi Purnamasari
**NIM:** 11221087
**Mata Kuliah:** Sistem Terdistribusi

## 📋 Deskripsi Proyek
Layanan **Event Aggregator** yang dibangun untuk memenuhi tugas UTS. Sistem ini berfungsi menerima ribuan event dari publisher, melakukan **deduplikasi** (menghapus data ganda), dan menyimpannya secara persisten.

**Fitur Utama:**
* **Idempotency:** Menjamin event dengan `event_id` yang sama hanya diproses sekali.
* **Persistence:** Data aman tersimpan di SQLite meskipun container di-restart.
* **Asynchronous:** Menggunakan Python `asyncio` dan `FastAPI` untuk performa tinggi.
* **Dockerized:** Lingkungan terisolasi aman menggunakan non-root user.

---

## 🎥 Video Demo
**Link YouTube:** [PASTE LINK VIDEO KAMU DISINI]

*(Video mencakup: Build image, Demo pengiriman 5.500+ event, Bukti deduplikasi berjalan, dan Test restart container)*

---

## 🚀 Cara Menjalankan (How to Run)

### Opsi A: Menggunakan Docker Compose (Rekomendasi - Bonus Point)
Cara ini akan menjalankan **Server Aggregator** dan **Simulasi Publisher** secara otomatis.

1.  **Build & Run:**
    ```bash
    docker compose up --build
    ```
2.  **Observasi:**
    * Lihat terminal. Anda akan melihat log pengiriman event.
    * Perhatikan log `WARNING:aggregator:Dropped DUPLICATE` yang menandakan sistem berhasil menolak data ganda.
3.  **Cek Statistik:**
    Buka terminal baru, lalu ketik:
    ```bash
    curl -s http://localhost:8080/stats
    ```
4.  **Stop Aplikasi:**
    Tekan `Ctrl+C` atau jalankan `docker compose down`.

### Opsi B: Menjalankan Unit Test
Untuk memvalidasi logika sistem secara otomatis:

```bash
# 1. Buat environment (opsional)
python3 -m venv .venv
source .venv/bin/activate

# 2. Install library
pip install -r requirements.txt

# 3. Jalankan Test
pytest