# DevOpsHub — Security & Hardening Reference

Dokumen ini menjelaskan arsitektur keamanan, perlindungan multi-tenant, manajemen rahasia (*secret management*), dan proteksi terhadap serangan injeksi pada platform DevOpsHub.

---

## 1. Multi-Tenant Isolation & IDOR Protection

DevOpsHub menerapkan isolasi berbasis Workspace secara ketat di tingkat basis data dan layer API:
1. **Verifikasi Hierarki Setiap Request**:
   * Setiap endpoint memeriksa kepemilikan bertingkat:
     $$\text{User} \rightarrow \text{WorkspaceMember} \rightarrow \text{Workspace} \rightarrow \text{Environment} \rightarrow \text{Server} \rightarrow \text{Resource}$$
2. **Anti-IDOR (Insecure Direct Object Reference)**:
   * Pengguna tidak dapat memanipulasi UUID di URL untuk mengakses server atau environment milik workspace lain. Server query selalu memfilter `WHERE id = :server_id AND workspace_id = :workspace_id`.
   * Akses lintas workspace secara otomatis menghasilkan HTTP `404 Not Found` (mencegah enumerasi resource).

---

## 2. Role-Based Access Control (RBAC)

Matrix hak akses tim dalam setiap workspace:

| Operasi / Modul | OWNER | ADMIN | DEVELOPER | VIEWER |
| :--- | :---: | :---: | :---: | :---: |
| **Kelola Member & Role** | ✅ | ✅ | ❌ | ❌ |
| **Buat / Hapus Server & Env** | ✅ | ✅ | ❌ | ❌ |
| **Enroll & Revoke Agent** | ✅ | ✅ | ❌ | ❌ |
| **Lihat Monitoring & Metrik** | ✅ | ✅ | ✅ | ✅ |
| **Lihat Logs (Journal & Docker)** | ✅ | ✅ | ✅ | ✅ |
| **Start / Stop / Restart Service** | ✅ | ✅ | ❌ | ❌ |
| **Mutasi Docker Container** | ✅ | ✅ | ❌ | ❌ |
| **Trigger Deployment** | ✅ | ✅ | ❌ | ❌ |
| **Trigger Backup & Restore** | ✅ | ✅ | ❌ | ❌ |
| **Kelola Alert Rules** | ✅ | ✅ | ❌ | ❌ |
| **Lihat Security Audit Logs** | ✅ | ✅ | ❌ | ❌ |

---

## 3. Secret Management & Enkripsi Data

* **Enkripsi Kredensial Simetris (Fernet 256-bit AES)**:
  * SSH password, private key, dan passphrase disimpan dalam bentuk *ciphertext* terenkripsi di PostgreSQL (`server_credentials`).
  * Kunci dekripsi hanya dibaca di in-memory saat koneksi remote sedang diuji atau dijalankan.
* **Auto Redaction Secret**:
  * Response API dan log sistem secara otomatis menyaring key/token sensitif (seperti `password`, `token`, `secret`, `private_key`, `api_key`).
* **Zero Arbitrary Command Injection**:
  * Baik SSH maupun Agent **tidak menggunakan shell bebas (`shell=True`)**.
  * Semua interaksi remote menggunakan argumen list terproteksi dan predefined safe scripts.

---

## 4. Keamanan Jaringan & Firewall

| Port | Protokol | Akses | Keterangan |
| :---: | :---: | :---: | :--- |
| **443** | TCP (HTTPS) | Publik / Internet | TLS Reverse Proxy Nginx |
| **80** | TCP (HTTP) | Publik / Internet | Redirect 301 ke HTTPS |
| **22** | TCP (SSH) | Dibatasi / Private | Khusus akses admin host jika diperlukan |
| **5432** | TCP (PostgreSQL)| Internal Only | Tidak diekspos ke publik |
| **6379** | TCP (Redis) | Internal Only | Tidak diekspos ke publik |

---

## 5. Perlindungan Rate Limiting & Security Headers

* **Rate Limiter (Token Bucket / IP Window)**:
  * Endpoint Login: Maks 10 req/menit per IP.
  * Endpoint Register: Maks 5 req/menit per IP.
  * Endpoint Refresh: Maks 20 req/menit per IP.
  * Operasi Sensitif: Maks 30 req/menit per IP.
* **Security Headers**:
  * `Strict-Transport-Security: max-age=31536000; includeSubDomains; preload`
  * `X-Content-Type-Options: nosniff`
  * `X-Frame-Options: DENY`
  * `Referrer-Policy: strict-origin-when-cross-origin`
  * `X-XSS-Protection: 1; mode=block`
