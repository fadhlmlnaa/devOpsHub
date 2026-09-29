# DevOpsHub — Database Backup & Restore Guide

Dokumen ini menjelaskan strategi pencadangan data (*backup*), verifikasi integritas checksum SHA256, dan prosedur pemulihan bencana (*restore*) pada basis data PostgreSQL DevOpsHub.

---

## 1. Strategi Backup Otomatis

Pencadangan database dilakukan secara reguler menggunakan format binary terkompresi `pg_dump -F c`.

### 1.1 Menjalankan Backup Manual
```bash
./scripts/backup_db.sh
```
Output:
* File backup: `./backups/db/devopshub_devops_backup_YYYYMMDD_HHMMSS.dump`
* File checksum: `./backups/db/devopshub_devops_backup_YYYYMMDD_HHMMSS.dump.sha256`

### 1.2 Menjadwalkan Backup Otomatis via Cron (Setiap Hari Pukul 02:00 UTC)
Tambahkan ke `crontab -e`:
```bash
0 2 * * * /opt/devopshub/scripts/backup_db.sh >> /var/log/devopshub_backup.log 2>&1
```

---

## 2. Prosedur Restore Database

### 2.1 Menjalankan Restore
Untuk memulihkan database dari file `.dump`:
```bash
./scripts/restore_db.sh ./backups/db/devopshub_devops_backup_20260929_155940.dump
```

Langkah yang dieksekusi secara otomatis oleh script:
1. **Verifikasi Checksum**: Memastikan file dump tidak korup (`shasum -a 256 -c`).
2. **Isolasi Temp DB**: Melakukan restore ke `devops_restore_temp` terlebih dahulu agar tidak merusak data live jika terjadi kegagalan restore.
3. **Atomic Swap**: Menghentikan koneksi aktif lama dan menukar temp database menjadi database utama `devops`.
4. **Smoke Queries**: Menampilkan jumlah baris pada tabel inti (`users`, `workspaces`, `servers`, `audit_logs`).

---

## 3. Retensi & Penyimpanan Offsite

1. **Retensi Lokal**: Script secara otomatis menghapus file dump lokal yang berumur lebih dari **30 hari**.
2. **Rekomendasi Offsite Sync (S3 / Cloud Storage)**:
   Gunakan alat sinkronisasi seperti `aws s3 sync` atau `rclone`:
   ```bash
   rclone sync ./backups/db remote-s3:my-devopshub-backups/db/
   ```
