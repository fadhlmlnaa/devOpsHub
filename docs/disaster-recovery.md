# DevOpsHub — Disaster Recovery (DR) Plan

Dokumen ini mendokumentasikan skenario kegagalan sistem, target pemulihan, dan langkah-langkah mitigasi darurat.

---

## 1. Recovery Objectives (RPO & RTO)

| Metrik | Target | Definisi |
| :--- | :---: | :--- |
| **RPO (Recovery Point Objective)** | **< 24 Jam** | Maksimal kehilangan data yang dapat ditoleransi (berdasarkan backup harian). |
| **RTO (Recovery Time Objective)** | **< 30 Menit** | Durasi maksimal untuk mengembalikan sistem beroperasi penuh setelah bencana. |

---

## 2. Skenario Kegagalan & Penanganan

### Skenario 1: Server Host / VPS Utama Rusak Total
1. Siapkan server VPS baru dengan Docker & Docker Compose.
2. Clone repositori ke `/opt/devopshub`.
3. Salin file `.env` (pastikan menyimpan backup offline dari `.env` dan `CREDENTIAL_ENCRYPTION_KEY`).
4. Unduh file backup database terbaru dari S3 / offsite storage.
5. Jalankan `docker compose -f docker-compose.prod.yml up -d postgres`.
6. Eksekusi `./scripts/restore_db.sh <backup_file.dump>`.
7. Jalankan seluruh service: `docker compose -f docker-compose.prod.yml up -d`.
8. Seluruh Agent yang sedang aktif di VPS remote akan otomatis melakukan reconnect via WebSocket tanpa perlu konfigurasi ulang.

### Skenario 2: Database PostgreSQL Korup
1. Hentikan container API & Worker:
   ```bash
   docker compose -f docker-compose.prod.yml stop api worker
   ```
2. Jalankan restore database dari backup snapshot terakhir:
   ```bash
   ./scripts/restore_db.sh ./backups/db/devopshub_backup_latest.dump
   ```
3. Nyalakan kembali API & Worker:
   ```bash
   docker compose -f docker-compose.prod.yml start api worker
   ```
4. Jalankan smoke test: `python3 ./scripts/smoke_test.py https://api.domainanda.com`.

### Skenario 3: Kehilangan `CREDENTIAL_ENCRYPTION_KEY`
> [!CAUTION]
> Kunci enkripsi Fernet (`CREDENTIAL_ENCRYPTION_KEY`) digunakan untuk mengenkripsi password SSH dan SSH private key tersimpan di database. Jika kunci ini hilang:
> 1. Data akun, workspace, environment, dan agent tokens **tetap aman**.
> 2. Namun password SSH dan SSH private key yang tersimpan **tidak dapat didekripsi kembali**.
> 3. **Solusi**: Generate key baru, simpan ke `.env`, lalu perbarui kredensial SSH pada masing-masing server di aplikasi mobile (atau beralih sepenuhnya ke mode DevOps Agent).

---

## 3. Disaster Recovery Checklist & Drill

Jalankan simulasi pemulihan bencana setiap kuartal (3 bulan sekali):
- [ ] Unduh backup terbaru dari offsite storage.
- [ ] Spin up VPS/staging sementara.
- [ ] Lakukan restore database.
- [ ] Uji login dan query data.
- [ ] Hancurkan environment uji coba.
