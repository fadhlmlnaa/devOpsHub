# DevOpsHub — Production Readiness Checklist

Checklist wajib sebelum meluncurkan (*go-live*) platform DevOpsHub ke lingkungan production.

---

## 📋 Pre-Launch Verification Matrix

### 1. Networking & Domain
- [x] Domain dan DNS record terkonfigurasi (A/CNAME record mengarah ke IP host).
- [x] HTTPS / TLS termination aktif dengan sertifikat valid (Let's Encrypt / Commercial SSL).
- [x] HTTP (port 80) otomatis melakukan 301 Redirect ke HTTPS (port 443).
- [x] WebSocket upgrade `/api/v1/agent/ws` berhasil dilewati oleh Nginx reverse proxy.
- [x] Port 5432 (PostgreSQL) dan Port 6379 (Redis) tertutup rapat dari akses internet publik.

### 2. Environment & Secret Hardening
- [x] `APP_ENV=production` diset pada file `.env`.
- [x] `JWT_SECRET_KEY` diisi dengan random key minimal 32 karakter (bukan nilai default / `change_me`).
- [x] `CREDENTIAL_ENCRYPTION_KEY` di-generate baru menggunakan Fernet base64 key.
- [x] `AGENT_SECRET_KEY` di-generate baru untuk penandatanganan token HMAC.
- [x] `CORS_ALLOWED_ORIGINS` hanya memuat domain resmi aplikasi (tanpa wildcard `*`).
- [x] Startup security validation aktif dan menggagalkan boot jika konfigurasi tidak aman.

### 3. Database & Reliability
- [x] Skema database termigrasi penuh dengan `alembic upgrade head`.
- [x] Database connection pooling (`pool_size=20`, `max_overflow=10`) terkonfigurasi.
- [x] Backup script otomatis (`scripts/backup_db.sh`) diuji dan menghasilkan checksum valid.
- [x] Restore script (`scripts/restore_db.sh`) diuji dan lulus uji query integritas data.
- [x] Kebijakan retensi data (`AUDIT_RETENTION_DAYS=90`, `JOB_RETENTION_DAYS=60`) aktif.

### 4. Application Server & Background Worker
- [x] Multi-worker ASGI (`WEB_CONCURRENCY=2` atau lebih) aktif.
- [x] Background worker (`worker.py`) berjalan secara terpisah untuk alert rules dan maintenance.
- [x] Liveness probe (`GET /api/v1/health/live`) merespons HTTP 200 dengan `X-Request-ID`.
- [x] Readiness probe (`GET /api/v1/health/ready`) memvalidasi status koneksi DB & Redis.
- [x] Rate limiting aktif pada endpoint autentikasi dan mutasi sensitif.
- [x] Security headers (HSTS, nosniff, DENY, X-XSS-Protection) aktif.

### 5. Mobile Client (Flutter)
- [x] API URL production di-pass via compile-time flag: `--dart-define=API_BASE_URL=https://api.domainanda.com/api/v1`.
- [x] Token autentikasi tersimpan aman di `FlutterSecureStorage` (Encrypted SharedPreferences / Keychain).
- [x] Error handling terpusat menampilkan pesan ramah tanpa membocorkan trace/query.
- [x] `flutter analyze` dan `flutter test` lulus 100% tanpa issue.

### 6. DevOps Agent
- [x] Mode Outbound TLS/WebSocket teruji dari Linux VPS target.
- [x] Replay attack guard (nonce) dan expired job cleanup teruji.
- [x] Strict allowlist operations (tanpa arbitrary shell execution) terverifikasi.
- [x] Systemd auto-restart service (`devops-agent.service`) terkonfigurasi di server target.

---

## 🎯 Status Keseluruhan: **PRODUCTION READY (100%)**
