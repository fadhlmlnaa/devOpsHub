# Security Hardening & Audit Checklist — DevOpsHub

DevOpsHub telah menerapkan serangkaian kontrol keamanan tingkat enterprise (*defense-in-depth*) untuk memastikan platform aman, terisolasi secara multi-tenant, dan memenuhi standar audit perbankan/fintech.

---

## 1. Authentication & Token Management
- [x] **Secure Password Hashing**: Menggunakan algoritma bcrypt/Argon2 dengan salting otomatis.
- [x] **Short-Lived Access Tokens**: Token JWT akses memiliki masa berlaku singkat (default: 30 menit).
- [x] **Refresh Token Rotation**: Setiap kali token di-refresh, refresh token lama segera dibatalkan (*revoked*) dan diterbitkan refresh token baru.
- [x] **Token Family Reuse Detection**: Jika refresh token yang sudah dibatalkan digunakan kembali (indikasi pencurian token), seluruh *family session* pengguna terkait segera dibatalkan secara otomatis.
- [x] **Rate Limiting pada Auth Endpoints**: Login, Register, dan Refresh dilindungi dengan *sliding window rate limiter* (default: 5 percobaan per menit per IP/identifier) untuk mencegah serangan brute-force dan credential stuffing.

---

## 2. Authorization, Multi-Tenancy & RBAC
- [x] **Strict Multi-Tenancy Workspace Isolation**: Semua data (server, service, docker, deployment, backup, alert, audit) terikat pada `workspace_id`. Pengguna tidak dapat mengakses aset workspace lain.
- [x] **IDOR Prevention (Insecure Direct Object Reference)**: Setiap query dan mutasi memverifikasi kepemilikan aset terhadap workspace aktif pengguna.
- [x] **Role-Based Access Control (RBAC)**:
  - **OWNER**: Akses penuh, manajemen member workspace, audit log, konfigurasi sensitif.
  - **ADMIN**: Akses operasional penuh, audit log, manajemen server dan deployment.
  - **OPERATOR**: Eksekusi operasi operasional terotorisasi (restart service, deploy, trigger backup). Tidak dapat membaca audit log atau mengelola user.
  - **VIEWER**: Akses baca-saja (*read-only*) ke dashboard, metriks, status server/service. Dilarang melakukan mutasi apa pun.

---

## 3. Secret Protection & Anti-Arbitrary Execution
- [x] **Encryption at Rest**: SSH private keys dan kredensial sensitif dienkripsi menggunakan AES-256-GCM / Fernet sebelum disimpan ke database.
- [x] **Recursive Secret Redaction**: Modul `SecretRedactor` secara otomatis membersihkan kunci rahasia (`password`, `token`, `secret`, `private_key`, `api_key`, dll.) dari log, payload metadata audit, dan respons API.
- [x] **Zero Arbitrary Shell Execution**: Tidak ada endpoint yang mengeksekusi shell mentah (`sh -c`, `bash -c`). Seluruh eksekusi remote berbasis perintah yang telah didefinisikan secara statis (*whitelisted commands*).
- [x] **Masked Output**: Log eksekusi dan output backup yang mengandung credential otomatis disanitasi sebelum ditampilkan ke client.

---

## 4. Input Validation & Path Traversal Defense
- [x] **Safe Identifier Validation**: Nama container, service, nama branch, dan project ID divalidasi menggunakan regex ketat `^[a-zA-Z0-9_.-]+$` untuk mencegah command injection.
- [x] **Path Traversal Protection**: Direktori backup, path docker compose, dan deployment path divalidasi dan dinormalisasi untuk menolak karakter traversal seperti `..`, `~`, atau karakter kontrol ilegal.
- [x] **Pydantic Model Constraints**: Semua input request diserialisasi dan divalidasi tipe data serta batas panjangnya.

---

## 5. API Hardening & Middleware
- [x] **Security Headers**:
  - `X-Content-Type-Options: nosniff`
  - `X-Frame-Options: DENY` (mencegah Clickjacking)
  - `Referrer-Policy: strict-origin-when-cross-origin`
  - `X-XSS-Protection: 1; mode=block`
- [x] **CORS Hardening**: Origin yang diizinkan dikonfigurasi secara eksplisit melalui environment `CORS_ALLOWED_ORIGINS` (bukan wildcard `*` di mode produksi).
- [x] **Global Error Masking**: Pesan error exception internal tidak membocorkan stack trace database atau path server ke pengguna umum.

---

## 6. Centralized Append-Only Audit Logging
- [x] **Append-Only Immutability**: Tabel `audit_logs` tidak menyediakan endpoint `PUT`, `PATCH`, atau `DELETE`. Catatan audit permanen dan tidak dapat dimanipulasi melalui API.
- [x] **Comprehensive Event Auditing**: Mencatat seluruh aksi penting:
  - Auth: `LOGIN`, `LOGIN_FAILED`, `REGISTER`, `TOKEN_REFRESH`, `LOGOUT`
  - Server: `CREATE_SERVER`, `UPDATE_SERVER`, `DELETE_SERVER`, `TEST_SSH`
  - Services: `SERVICE_ACTION` (start/stop/restart/reload/enable/disable)
  - Docker: `CONTAINER_ACTION`, `COMPOSE_ACTION` (up/down/restart)
  - Deployments: `TRIGGER_DEPLOYMENT`, `CANCEL_DEPLOYMENT`
  - Backups: `TRIGGER_BACKUP`, `RESTORE_BACKUP`, `DELETE_BACKUP`
  - Alerts: `CREATE_ALERT_RULE`, `UPDATE_ALERT_RULE`, `DELETE_ALERT_RULE`, `ACKNOWLEDGE_ALERT`
  - Workspaces: `UPDATE_MEMBER_ROLE`, `REMOVE_MEMBER`
- [x] **Rich Context Metadata**: Setiap record audit mencatat:
  - `user_id`, `workspace_id`, `action`, `resource_type`, `resource_id`, `status`
  - `ip_address` & `user_agent`
  - `created_at` timestamp
  - `metadata` (tersanitasi/redacted)
- [x] **Audit Access Control**: Hanya role `OWNER` dan `ADMIN` yang memiliki izin membaca audit log.
- [x] **Mobile Audit Explorer**: Antarmuka visual di aplikasi mobile Flutter untuk filter berdasarkan action, resource, date range, dan melihat detail metadata audit secara aman.
