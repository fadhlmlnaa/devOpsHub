# DevOpsHub — Troubleshooting & Operations Runbook

Panduan pemecahan masalah operasional dan diagnosis kendala teknis pada platform DevOpsHub.

---

## 1. Masalah Umum & Solusi Cepat

### 1. Error 502 Bad Gateway pada Nginx / Reverse Proxy
* **Penyebab**: Container `api` (FastAPI) sedang dalam status restarting, startup error, atau gagal terhubung ke PostgreSQL/Redis.
* **Diagnosis**:
  ```bash
  docker logs devopshub_api --tail 100
  ```
* **Solusi**:
  1. Cek apakah ada konfigurasi secret tidak valid di `.env` (misal JWT_SECRET_KEY terlalu pendek saat `APP_ENV=production`).
  2. Pastikan database PostgreSQL dalam status healthy: `docker ps`.

---

### 2. DevOps Agent di VPS Remote Gagal Terhubung (*Offline*)
* **Penyebab**: URL server tidak dapat dijangkau oleh VPS, DNS belum resolve, atau token enrollment sudah kedaluwarsa.
* **Diagnosis di Terminal VPS**:
  ```bash
  sudo systemctl status devops-agent
  # atau cek log:
  journalctl -u devops-agent -n 50 --no-pager
  ```
* **Solusi**:
  1. Cek apakah server URL bisa di-ping/curl dari VPS:
     ```bash
     curl -i https://api.domainanda.com/api/v1/health/live
     ```
  2. Jika token kedaluwarsa, buka aplikasi mobile di halaman Server Detail -> Klik **Enroll / Token Baru** -> Jalankan perintah enroll ulang di VPS.

---

### 3. Database Migration Gagal (*Alembic Collision*)
* **Penyebab**: Perubahan skema manual atau database tertinggal beberapa revisi.
* **Solusi**:
  ```bash
  # Cek current revision:
  docker compose -f docker-compose.prod.yml exec api alembic current

  # Upgrade ke head:
  docker compose -f docker-compose.prod.yml exec api alembic upgrade head
  ```

---

### 4. RenderFlex Overflow pada Aplikasi Mobile
* **Penyebab**: Teks meluap pada layar perangkat dengan lebar sempit (< 360dp) atau font scale besar.
* **Solusi**: Semua elemen aksi pada card server dan agent telah dibungkus dengan `Expanded`, `Wrap`, dan tata letak multi-baris responsif di codebase Flutter terkini.

---

## 2. Perintah Diagnosis Cepat

```bash
# Cek semua container aktif:
docker compose -f docker-compose.prod.yml ps

# Pantau live logs seluruh service:
docker compose -f docker-compose.prod.yml logs -f --tail 50

# Cek penggunaan CPU & Memory container:
docker stats --no-stream

# Jalankan automated smoke test:
python3 ./scripts/smoke_test.py https://api.domainanda.com
```
