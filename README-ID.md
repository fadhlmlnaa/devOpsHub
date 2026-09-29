# Dokumentasi Platform Mobile DevOps (DevOpsHub)

Platform DevOps Mobile modular dan company-agnostic yang dirancang untuk memberikan akses cepat kepada developer dan tim operations untuk memonitor dan mengelola infrastruktur langsung dari perangkat mobile.

[🧪 Panduan Testing Mandiri (README-TEST-ID.md)](file:///Users/fadhilmaulana/MyProject/DevOpsHub/README-TEST-ID.md)

> **Status Terkini**: **Step 05 — Flutter Foundation, Authentication & Workspace Selection**. Implementasi aplikasi mobile Flutter lengkap dengan GetX untuk State Management & Routing, Dio API Client terpusat dengan mekanisme single-flight refresh lock & token rotation, enkripsi `flutter_secure_storage`, tipografi **Plus Jakarta Sans**, dan **Base Widgets** sesuai palet warna logo brand (Deep Dark Teal & Electric Cyan).

---

## 1. Arsitektur Flutter Mobile (Step 05)

Struktur folder disusun secara modular, terpisah antara Core, Data, Modules, dan UI Presentation:

```text
mobile/
└── lib/
    ├── main.dart                      # Inisialisasi GetMaterialApp, Dark Theme & InitialBinding
    │
    ├── app/
    │   ├── routes/
    │   │   ├── app_pages.dart         # Konfigurasi rute dan binding GetX
    │   │   └── app_routes.dart        # Konstanta nama route
    │   └── theme/
    │       ├── app_colors.dart        # Palet warna logo brand (Teal, Cyan, Dark Surface)
    │       └── app_theme.dart         # Tema gelap dengan Plus Jakarta Sans
    │
    ├── core/
    │   ├── constants/
    │   │   └── app_constants.dart     # Base URL (Android/iOS/Web) & Key Secure Storage
    │   ├── network/
    │   │   ├── api_client.dart        # Dio interceptor, auto JWT injection & refresh lock
    │   │   └── api_exception.dart     # Safe user-friendly error mapping
    │   ├── storage/
    │   │   └── secure_storage_service.dart # Enkripsi Keychain/KeyStore
    │   └── widgets/                   # Base Widgets Reusable
    │       ├── app_button.dart        # Button (Filled, Outline, Loading State)
    │       ├── app_text_field.dart    # Input Form (Prefix/Suffix, Validator, Toggle Password)
    │       ├── app_app_bar.dart       # Reusable AppBar dengan subtle border
    │       ├── app_bottom_sheet.dart  # Container modal bottom sheet dengan drag handle
    │       ├── app_card.dart          # Teal surface card container
    │       └── app_status_badge.dart  # Role badge (OWNER, ADMIN, DEVELOPER, VIEWER)
    │
    ├── data/
    │   ├── models/                    # Serialisasi JSON model backend
    │   │   ├── user_model.dart
    │   │   ├── auth_token_model.dart
    │   │   ├── workspace_model.dart
    │   │   └── workspace_member_model.dart
    │   └── services/
    │       ├── auth_service.dart      # HTTP Service Login, Register, Refresh, Logout, Me
    │       └── workspace_service.dart # HTTP Service Workspace CRUD
    │
    ├── modules/
    │   ├── splash/                    # Startup session verification & redirect
    │   ├── auth/                      # Login & Register views + AuthController
    │   └── workspace/                 # Workspace list, create sheet & Workspace Home view
    │
    └── bindings/
        ├── initial_binding.dart       # Core service dependency injection
        ├── auth_binding.dart
        └── workspace_binding.dart
```

---

## 2. Alur Kerja Aplikasi (Flow Step 05)

```text
Buka Aplikasi (Splash)
         ↓
  Cek Sesi di SecureStorage
         ↓
┌─────────────────────────────────┐
│ Belum Login / Sesi Habis        │
│       ↓                         │
│ Layar Login (/auth/login)       │
│       ↓                         │
│ POST /auth/login (API)          │
│       ↓                         │
│ Simpan Token di Secure Storage  │
└─────────────────────────────────┘
         ↓
  Daftar Workspace (/workspaces)
  (Tampil Role: OWNER, ADMIN, dll)
         ↓
  Pilih / Buat Workspace
         ↓
  Workspace Home (/workspaces/:id)
  (Environment & Server Management aktif di Step 06)
```

---

## 3. Fitur Keamanan & Arsitektur Step 06 (Server Management & SSH Connection)

1. **Workspace Scoped Environment & Server CRUD**:
   - Environment dan Server diisolasi secara ketat per workspace.
   - Cross-workspace validation: Server tidak dapat dihubungkan ke environment yang berada di workspace berbeda.
   - Deletion Protection: Environment tidak dapat dihapus jika masih memiliki server terdaftar.
2. **Enkripsi Kredensial Server (Zero-Plaintext at Rest)**:
   - Abstraksi tabel `server_credentials` yang terpisah dari tabel `servers`.
   - Enkripsi simetrik berbasis Fernet (`cryptography`) menggunakan `CREDENTIAL_ENCRYPTION_KEY`.
   - Mendukung autentikasi `PASSWORD` dan `PRIVATE_KEY` (dengan passphrase opsional).
   - Password dan private key **tidak pernah** dikembalikan melalui API response dan tidak pernah dicatat ke logging.
3. **SSH Provider Abstraction**:
   - Desain arsitektur `ConnectionProvider` (abstract base class) -> `SSHProvider` (`asyncssh`) -> Server target.
   - Dirancang fleksibel untuk masa depan agar dapat diperluas ke `AgentProvider` (DevOps Agent) tanpa menulis ulang business logic.
4. **SSH Connection Testing & System Info**:
   - Endpoint `POST /api/v1/workspaces/{workspace_id}/servers/{server_id}/connection-test` melakukan validasi jangkauan jaringan, autentikasi SSH, dan mengekstrak informasi dasar server (`hostname`, `operating_system`, `kernel`, `architecture`, `uptime`).
   - Dilengkapi strict timeout: `SSH_CONNECT_TIMEOUT` dan `SSH_COMMAND_TIMEOUT`.
   - **Tidak ada arbitrary shell endpoint**: Keamanan terjamin tanpa celah eksekusi arbitrary command dari client.
6. **Step 07 — Server Monitoring & System Metrics**:
   - Real-time telemetry monitoring: CPU usage & cores count, RAM / Memory bytes & percentage, Disk storage `/` bytes & percentage, Load Average (1m, 5m, 15m), Uptime in seconds & human-readable format, System specification (OS, Kernel, Arch, Hostname), and Network interfaces.
   - Endpoint: `GET /api/v1/workspaces/{workspace_id}/servers/{server_id}/metrics`.
   - Single SSH Connection Session: Menjalankan predefined batch telemetry probe script dengan overhead jaringan dan latensi minimal (<0.1s).
   - Partial Metric Resilience: Kegagalan salah satu metrik (misal disk format) tidak menggagalkan metrik lainnya.
   - Zero Database Bloat: Tidak melakukan insert data historis per request.
   - Flutter Live Dashboard: Visual progress bar (cyan/mint), gauge metrics, offline diagnostics banner, manual refresh & pull-to-refresh.

7. **Step 08 — Service Management (Linux Systemd)**:
   - Manajemen siklus hidup unit service Linux systemd secara aman dari perangkat mobile (Start, Stop, Restart, Reload).
   - **Systemd Discovery & Status**:
     - `GET /api/v1/workspaces/{workspace_id}/servers/{server_id}/services` (filter: all, active, inactive, failed; limit <= 200).
     - `GET /api/v1/workspaces/{workspace_id}/servers/{server_id}/services/{service_name}` (detail load state, active state, sub state, PID, enabled status, active timestamp).
   - **Lifecycle Actions**:
     - `POST /api/v1/workspaces/{workspace_id}/servers/{server_id}/services/{service_name}/start`
     - `POST /api/v1/workspaces/{workspace_id}/servers/{server_id}/services/{service_name}/stop`
     - `POST /api/v1/workspaces/{workspace_id}/servers/{server_id}/services/{service_name}/restart`
     - `POST /api/v1/workspaces/{workspace_id}/servers/{server_id}/services/{service_name}/reload`
   - **Keamanan & Guarding**:
     - **Strict Whitelist Validation**: Service name wajib sesuai regex `^[A-Za-z0-9_.@:-]+\.service$`. Menolak karakter berbahaya (`;`, `&&`, `|`, `$()`, backticks, `/`, spasi, path traversal).
     - **Explicit Confirmation Guard**: Seluruh mutasi membutuhkan payload `{"confirm": true}`.
     - **Sudo / Privilege Handling**: Mendukung user `root` atau user dengan `passwordless sudo` (`sudo -n systemctl ...`). Tidak menyimpan password sudo dalam plaintext. Jika sudo membutuhkan password interaktif, backend mengembalikan pesan error yang jelas dan aman.
     - **RBAC Matrix**: `VIEWER` dan `DEVELOPER` hanya memiliki izin baca (GET). Mutasi (Start, Stop, Restart, Reload) dibatasi hanya untuk `ADMIN` dan `OWNER` (HTTP 403 jika dilanggar).
     - **No Arbitrary Shell**: Backend hanya menjalankan perintah systemd terisolasi yang sudah didefinisikan. Tidak ada endpoint shell/command bebas.
   - **Flutter Mobile Integration**:
     - Service List View dengan search box, filter chips (Semua, Active, Inactive, Failed), dan pull-to-refresh.
     - Service Detail View dengan status badge dinamis (RUNNING, STOPPED, FAILED, UNKNOWN), spesifikasi unit systemd, dan action buttons interaktif.
     - Modal Dialog Konfirmasi dengan penjelasan dampak sebelum action dieksekusi.
     - State button otomatis dinonaktifkan (disabled) jika operasi tidak relevan dengan status saat ini atau user tidak memiliki role mutasi.

8. **Step 09 — Logs Management (Systemd Journal)**:
   - Pengambilan dan inspeksi log service Linux via `journalctl` secara aman dan terisolasi dari perangkat mobile.
   - **Log Retrieval API**:
     - `GET /api/v1/workspaces/{workspace_id}/servers/{server_id}/services/{service_name}/logs?lines=100&since=10m`
   - **Parameter & Filtering**:
     - `lines`: Batas jumlah baris (min: 10, max: 1000, default: 100).
     - `since`: Filter rentang waktu terdefinisi (`5m`, `10m`, `30m`, `1h`, `6h`, `12h`, `24h`).
     - `service_name`: Tervalidasi ketat `^[A-Za-z0-9_.@:-]+\.service$`.
   - **Fitur & Keamanan**:
     - **Secret Redaction Reusable (`SecretRedactor`)**: Masking otomatis terhadap data sensitif pada isi log (`password=********`, `token=********`, `api_key=********`, `Authorization: Bearer ********`, private key blocks).
     - **Size Limitation & Truncation**: Maksimal response dibatasi 1MB (`MAX_LOG_RESPONSE_BYTES=1048576`). Jika melampaui, log dipotong secara aman dan ditandai `truncated: true`.
     - **Fault Tolerance**: Parsing format log JSON/plain text yang fleksibel; baris log yang tidak sempurna tidak menggagalkan seluruh request.
     - **No Database Log Persistence**: Log tetap berada pada target server (*single source of truth*), mencegah penumpukan data di PostgreSQL.
   - **Flutter Mobile Log Viewer**:
     - Tampilan log monospace dengan color-coded priority badge (ERROR, WARNING, INFO, DEBUG).
     - Filter bar interaktif untuk memilih jumlah baris (`50`, `100`, `200`, `500`, `1000`) dan rentang waktu (`Semua`, `5m`, `10m`, `30m`, `1h`, `6h`, `24h`).
     - Filter pencarian instan dalam log (`Search`).
     - Salin baris log individual atau seluruh teks log ke clipboard.
     - Pull-to-refresh dan tombol manual refresh.

9. **Step 10 — Docker Management & Docker Compose**:
   - Pengelolaan container Docker dan Docker Compose Projects secara aman, terkontrol, dan real-time dari perangkat mobile.
   - **Docker Detection & Daemon Status**:
     - `GET /api/v1/workspaces/{workspace_id}/servers/{server_id}/docker` (Status: `RUNNING`, `STOPPED`, `NOT_INSTALLED`, `UNKNOWN`, serta versi daemon).
   - **Container Management**:
     - `GET /api/v1/workspaces/{workspace_id}/servers/{server_id}/docker/containers?state=running|stopped|all` (Discovery container aktif/terhenti).
     - `GET /api/v1/workspaces/{workspace_id}/servers/{server_id}/docker/containers/{container_id}` (Detail container, image, ports, restart policy, CPU/RAM usage).
     - `POST /api/v1/workspaces/{workspace_id}/servers/{server_id}/docker/containers/{container_id}/start`
     - `POST /api/v1/workspaces/{workspace_id}/servers/{server_id}/docker/containers/{container_id}/stop`
     - `POST /api/v1/workspaces/{workspace_id}/servers/{server_id}/docker/containers/{container_id}/restart`
     - `GET /api/v1/workspaces/{workspace_id}/servers/{server_id}/docker/containers/{container_id}/logs?lines=100&since=10m`
   - **Docker Compose Projects**:
     - `GET /api/v1/workspaces/{workspace_id}/servers/{server_id}/docker/compose/projects`
     - `POST /api/v1/workspaces/{workspace_id}/servers/{server_id}/docker/compose/projects` (Registrasi project dengan validasi path & nama).
     - `PATCH /api/v1/workspaces/{workspace_id}/servers/{server_id}/docker/compose/projects/{project_id}`
     - `DELETE /api/v1/workspaces/{workspace_id}/servers/{server_id}/docker/compose/projects/{project_id}`
     - `GET /api/v1/workspaces/{workspace_id}/servers/{server_id}/docker/compose/projects/{project_id}/status`
     - `POST /api/v1/workspaces/{workspace_id}/servers/{server_id}/docker/compose/projects/{project_id}/up`
     - `POST /api/v1/workspaces/{workspace_id}/servers/{server_id}/docker/compose/projects/{project_id}/down`
     - `POST /api/v1/workspaces/{workspace_id}/servers/{server_id}/docker/compose/projects/{project_id}/restart`
   - **Keamanan & Guarding**:
     - **Strict Regex Validation**: Validasi container ID (`^[a-zA-Z0-9][a-zA-Z0-9_.-]{0,127}$`), project name (`^[a-z0-9][a-z0-9_-]{0,63}$`), dan working directory wajib absolut path yang aman tanpa path traversal (`..`).
     - **Confirmation Guard**: Mutasi container & compose wajib menyertakan payload `{"confirm": true}`.
     - **Secret Redaction**: Output container logs secara otomatis disaring menggunakan `SecretRedactor` sebelum dikirim ke mobile.
     - **No Arbitrary Commands**: Tidak ada endpoint `docker exec`, `docker run`, `docker system prune`, ataupun shell bebas.
     - **RBAC Matrix**: `VIEWER` dan `DEVELOPER` hanya boleh melihat (read-only). Mutasi container & compose hanya untuk `ADMIN` dan `OWNER`.
   - **Flutter Mobile Integration**:
     - Docker Dashboard View dengan tab segmentasi (Containers vs Compose Projects).
     - Container Detail View dengan badge status, resource usage, ports list, dan action buttons (Start, Stop, Restart).
     - Monospace Container Log Viewer dengan color-coded timestamp dan search/filter/copy.
     - Compose Project Cards dengan status service-service di dalamnya dan action buttons (Up, Down, Restart).
     - Bottom sheet registrasi Compose Project baru.

10. **Step 11 — Deployment Management**:
    - **Tujuan**: Memungkinkan eksekusi deployment aplikasi secara aman, terprediksi, dan terkontrol dari perangkat mobile tanpa membuka celah eksekusi arbitrary shell command.
    - **Deployment Architecture**:
      ```text
      DeploymentManagementService
              ↓
      DeploymentProvider (Abstract Interface)
              ↓
      SSHDeploymentProvider
              ↓
      ConnectionProvider (Existing SSH Pool)
      ```
    - **Deployment Types**:
      - `SYSTEMD`: Workflow deployment untuk aplikasi berbasis Linux systemd service (e.g. Odoo, Laravel, Node.js, Python).
      - `DOCKER_COMPOSE`: Workflow deployment untuk aplikasi berbasis multi-container Docker Compose.
    - **Supported Predefined Operations**:
      - `GIT_PULL`: Menjalankan git pull pada branch terdaftar dengan kredensial server.
      - `INSTALL_DEPENDENCIES`: Menjalankan instalasi dependency terisolasi.
      - `BUILD`: Menjalankan kompilasi / build aset terisolasi.
      - `DOCKER_COMPOSE_PULL`: Menarik image compose terbaru.
      - `DOCKER_COMPOSE_UP`: Menjalankan compose up -d.
      - `RESTART_SERVICE`: Me-restart systemd unit service terdaftar.
      - `HEALTH_CHECK`: Memvalidasi status service, status docker compose, atau endpoint HTTP health check.
    - **Protected Environments**:
      - Kolom `is_protected` (Boolean) pada `environments`.
      - Deployment ke protected environment (misal Production) mewajibkan konfirmasi eksplisit (`confirm: true`), jika tidak request ditolak dengan `400 Bad Request`.
    - **Concurrency Protection**:
      - Lock level database/aplikasi: deployment berikutnya pada config yang sama akan ditolak dengan `409 Conflict` ("Deployment sedang berjalan.") selama status deployment sebelumnya masih `RUNNING`.
    - **Deployment Logs & Bounded Storage**:
      - Tabel `deployment_logs` mencatat log langkah demi langkah secara berurutan (`sequence`, `timestamp`, `level`, `message`).
      - Batas maksimal: `MAX_DEPLOYMENT_LOG_LINES=5000` dan `MAX_DEPLOYMENT_LOG_MESSAGE_LENGTH=4000`.
      - Masking data sensitif otomatis menggunakan `SecretRedactor` sebelum disimpan ke database.
    - **Timeouts**:
      - `DEPLOYMENT_CONNECTION_TIMEOUT=5s`
      - `DEPLOYMENT_COMMAND_TIMEOUT=60s`
      - `DEPLOYMENT_MAX_DURATION=1800s`
    - **RBAC Matrix**:
      - `VIEWER` & `DEVELOPER`: Read-only (Melihat konfigurasi, riwayat, dan detail log deployment).
      - `ADMIN` & `OWNER`: Full CRUD Konfigurasi Deployment & Menjalankan Deploy.
11. **Step 12 — Backup Management**:
    - **Tujuan**: Memungkinkan konfigurasi, eksekusi, inspeksi riwayat, monitoring log, dan verifikasi integritas backup server secara aman dan terkontrol langsung dari aplikasi mobile.
    - **Pernyataan Keamanan Krusial**:
      > **Platform ini TIDAK mengekspos arbitrary shell commands atau arbitrary file paths.** Semua operasi backup dibatasi pada whitelist operasi terdefinisi dan path/sumber yang terverifikasi.
    - **Backup Architecture**:
      ```text
      BackupManagementService
              ↓
      BackupProvider (Abstract Interface)
              ↓
      SSHBackupProvider (SSH Implementation)
              ↓
      ConnectionProvider (Existing SSH Pool)
      ```
    - **Supported Backup Types**:
      - `POSTGRESQL`: Backup database PostgreSQL terkontrol (`pg_dump` dengan kompresi gzip dan opsi autentikasi aman).
      - `FILESYSTEM`: Backup direktori sistem berkas aplikasi terkontrol (`tar -czf` dengan validasi path absolut dan pencegahan path traversal).
      - `DOCKER_VOLUME`: Backup volume Docker terkontrol (`docker run --rm -v volume:/data ... tar -czf`).
    - **Supported Predefined Operations**:
      - `POSTGRESQL_DUMP`: Operasi dump database PostgreSQL ke destinasi backup terdaftar.
      - `FILESYSTEM_ARCHIVE`: Operasi kompresi arsip folder direktori ke destinasi backup.
      - `DOCKER_VOLUME_BACKUP`: Operasi arsip volume container ke destinasi backup.
      - `VERIFY_BACKUP`: Operasi kalkulasi checksum SHA-256 dan verifikasi keberadaan berkas backup pada server.
    - **Backup Verification & Checksum Integrity**:
      - Setiap backup yang berhasil menghasilkan hash **SHA-256** dan mencatat ukuran berkas (`file_size_bytes`) serta metadata file.
      - Endpoint `POST /api/v1/workspaces/{workspace_id}/backups/{backup_id}/verify` memvalidasi keberadaan fisik berkas di server, mengkalkulasi ulang hash SHA-256 langsung di server, dan membandingkannya dengan hash yang tersimpan di database.
    - **Protected Environments**:
      - Pada environment dengan `is_protected = true`, backend mewajibkan konfirmasi eksplisit (`confirm: true`), jika tidak request ditolak dengan `400 Bad Request`.
    - **Concurrency Protection**:
      - Mencegah eksekusi ganda pada konfigurasi backup yang sama. Jika backup sedang berstatus `RUNNING`, request baru ditolak dengan `409 Conflict` ("Backup sedang berjalan.").
    - **Retention Metadata**:
      - Setiap konfigurasi mencatat `retention_days` (default: 7 hari). Metadata retensi disimpan dan siap untuk mekanisme pembersihan terisolasi di masa depan.
    - **Secret Redaction & Bounded Logging**:
      - Log backup disimpan pada tabel `backup_logs` dengan batasan `MAX_BACKUP_LOG_LINES=5000` dan `MAX_BACKUP_LOG_MESSAGE_LENGTH=4000`.
      - Seluruh kredensial (database password, SSH password, private key, bearer tokens) disaring secara otomatis menggunakan `SecretRedactor` sebelum disimpan ke database atau dikirim ke API response.
    - **Timeouts**:
      - `BACKUP_CONNECTION_TIMEOUT=5s`
      - `BACKUP_COMMAND_TIMEOUT=300s`
      - `BACKUP_MAX_DURATION=3600s`
    - **RBAC Matrix**:
      - `VIEWER` & `DEVELOPER`: Read-only (Melihat daftar konfigurasi, detail riwayat, status, dan log backup).
      - `ADMIN` & `OWNER`: Full CRUD Konfigurasi Target, Menjalankan Backup (`run`), dan Menjalankan Verifikasi (`verify`).
    - **Flutter Mobile Screens**:
      - **Backup Dashboard**: Segmented tabs ("Riwayat Backup" vs "Konfigurasi Target") dengan pencarian dan filter status/tipe.
      - **Confirmation Sheet**: Modal dialog dengan ringkasan target, estimasi operasi, dan banner peringatan protected environment.
      - **Backup Detail View**: Menampilkan status dinamis, nama file, ukuran terformat, waktu mulai/selesai, hash SHA-256 lengkap, tombol Verifikasi Berkas, dan tombol Lihat Log.
      - **Backup Config Form**: Form pendaftaran target baru dengan pemilih tipe (`PostgreSQL`, `Filesystem`, `Docker Volume`), label dinamis, switch kompresi gzip, dan validasi input.
      - **Monospace Terminal Viewer**: Log viewer real-time dengan status badge, filter level (INFO, WARNING, ERROR), copy to clipboard, dan manual refresh.

  - **Step 13 — Alerts & Notifications**:
    - **Arsitektur**:
      ```text
      Monitoring / Telemetry
                 │
                 ▼
      AlertEvaluationService
                 │
                 ▼
             AlertRule
                 │
                 ▼
            AlertState (FIRING / RESOLVED)
                 │
                 ▼
        NotificationService
                 ├── In-App Notification (Tabel notifications)
                 └── Email (Provider interface extensible)
      ```
    - **Supported Metrics**:
      - `CPU_USAGE`: Persentase pemakaian CPU server (0 - 100%).
      - `MEMORY_USAGE`: Persentase pemakaian RAM server (0 - 100%).
      - `DISK_USAGE`: Persentase pemakaian penyimpanan partisi disk utama (0 - 100%).
      - `LOAD_AVERAGE`: Beban rata-rata CPU 1-menit (`load1`).
      - `SERVER_STATUS`: Status server (`OFFLINE` = 0.0, `ONLINE` = 1.0).
      - `SERVICE_STATUS`: Status layanan systemd target (`target_identifier`, e.g. nginx, docker, redis: `FAILED/INACTIVE` = 0.0, `RUNNING` = 1.0).
      - `DEPLOYMENT_STATUS`: Status deployment terakhir pada server/workspace (`FAILED` = 0.0, `SUCCESS` = 1.0).
      - `BACKUP_STATUS`: Status operasi backup terakhir pada server/workspace (`FAILED` = 0.0, `SUCCESS` = 1.0).
    - **Supported Operators**:
      - `GREATER_THAN` (`>`), `GREATER_THAN_OR_EQUAL` (`>=`), `LESS_THAN` (`<`), `LESS_THAN_OR_EQUAL` (`<=`), `EQUAL` (`==`), `NOT_EQUAL` (`!=`).
    - **Duration Thresholding**:
      - Untuk mencegah alert spam dari lonjakan singkat (transient spikes), kondisi harus bertahan selama `duration_seconds` (contoh: CPU > 90% selama 300 detik) sebelum memicu pengiriman notifikasi.
    - **Alert Deduplication & Spam Protection**:
      - Satu kondisi yang terus terpenuhi dalam siklus evaluasi berturut-turut tetap menjadi 1 record alert aktif berstatus `FIRING` (tidak membuat record alert baru setiap evaluasi).
      - Notifikasi `FIRING` hanya dikirimkan 1 kali saat alert pertama kali memenuhi durasi.
      - Saat metrik kembali normal, alert otomatis berstatus `RESOLVED` dan mengirimkan 1 notifikasi resolusi.
      - Jika kondisi bermasalah terjadi kembali setelah resolusi, sistem dapat memicu alert baru (`RESOLVED -> FIRING`).
    - **Manual Alert Resolution**:
      - Endpoint `POST /api/v1/workspaces/{workspace_id}/alerts/{alert_id}/resolve` dengan `confirm: true` memungkinkan `ADMIN` atau `OWNER` menyelesaikan alert secara manual.
      - Resolusi manual tidak menonaktifkan aturan monitoring (`AlertRule`), sehingga alert akan menyala kembali jika kondisi masih bermasalah pada evaluasi selanjutnya.
    - **In-App Notifications & Preferences**:
      - Setiap pengguna memiliki preferensi mandiri (`notification_preferences`) untuk mengatur `in_app_enabled`, `email_enabled`, dan `minimum_severity` (`INFO`, `WARNING`, `CRITICAL`).
      - Pengguna hanya dapat membaca dan menandai dibaca notifikasi miliknya sendiri (User Isolation).
    - **Background Scheduler & Configuration**:
      - `ALERT_EVALUATION_INTERVAL_SECONDS=60`
      - `ALERT_ENABLE_BACKGROUND_SCHEDULER=True`
      - `MAX_NOTIFICATIONS_LIMIT=100`
    - **RBAC Matrix**:
      - `VIEWER` & `DEVELOPER`: Read-only (Melihat alert firing/resolved, timeline audit event, aturan rules, dan preferensi notifikasi).
      - `ADMIN` & `OWNER`: Full CRUD Aturan Alert Rules dan Manual Alert Resolution.
    - **Flutter Mobile Screens**:
      - **Alert Dashboard**: Tab "Alert Aktif / Riwayat" dan Tab "Aturan Rules" dengan filter chips (Status, Severity), live badge unread, dan FAB Buat Aturan.
      - **Alert Detail View**: Informasi metrik lengkap, waktu terpicu, nilai batas vs terdeteksi, timeline audit event, dan tombol konfirmasi resolusi manual.
      - **Alert Rule Form**: Pembuat aturan fleksibel dengan pemilih metrik, operator, threshold, durasi detik, severity, dan target scope (server/environment).
      - **Notification Inbox**: Inbox in-app notification dengan filter unread, tombol "Tandai Semua Dibaca", dan bottom sheet preferensi notifikasi.
      - **AppBar Badges**: Indikator lonceng notifikasi dinamis 🔔 dengan unread counter badge.
  - **Step 14: Security Hardening & Audit Logging (TERBARU)**:
    - **Tujuan**: Memastikan platform aman, data rahasia terproteksi (*defense-in-depth*), aksi penting tercatat (*append-only audit*), dan tidak ada eksekusi perintah berbahaya/arbitrer.
    - **Arsitektur Keamanan**:
      ```text
      FastAPI Request -> Rate Limiting Middleware (429)
                      -> Security Headers Middleware (nosniff, DENY, etc.)
                      -> CORS Whitelist Validation
                      -> JWT Auth & Token Family Rotation / Reuse Detection
                      -> Multi-Tenant Workspace & RBAC Isolation
                      -> Input Validation (Anti-Traversal & Safe Identifiers)
                      -> Operation Execution (Predefined static commands only)
                      -> Redacted Audit Log Entry (Append-Only)
      ```
    - **Fitur Keamanan Utama**:
      - **Append-Only Audit Logging**: Seluruh operasi sensitif (Auth, Server CRUD, Service action, Docker/Compose action, Deployment, Backup, Alert rules, Workspace roles) otomatis dicatat di tabel `audit_logs` bersama metadata IP, User Agent, Timestamp, Workspace, dan Actor. Endpoint audit bersifat *read-only* khusus untuk role `OWNER` dan `ADMIN`. Tidak ada endpoint update/delete audit log.
      - **Token Rotation & Family Session Revocation**: Refresh token lama langsung di-revoke saat refresh. Jika token lama dipakai ulang (indikasi pencurian token), seluruh token dalam *family* tersebut dibatalkan otomatis.
      - **Automatic Recursive Secret Redaction**: Password, token, private key, secret, dan credential otomatis disanitasi (`[REDACTED]`) sebelum disimpan di metadata audit log atau ditampilkan di respons/log aplikasi.
      - **Zero Arbitrary Shell Execution**: Tidak ada endpoint remote shell mentah. Seluruh aksi remote dibatasi pada *whitelisted predefined operational actions*.
      - **Input Validation & Path Traversal Protections**: Regex ketat untuk identifier sistem serta normalisasi path untuk menolak `..` dan karakter berbahaya.
      - **Sliding Window Rate Limiter**: Membatasi brute-force pada endpoint autentikasi (`AUTH_RATE_LIMIT_LOGIN_MAX=5/menit`, `AUTH_RATE_LIMIT_REGISTER_MAX=3/menit`, `OPERATION_RATE_LIMIT=120/menit`).
      - **Security Headers & CORS**: `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: strict-origin-when-cross-origin`, `X-XSS-Protection: 1; mode=block`.
    - **Flutter Mobile Screens**:
      - **Audit Logs Explorer**: Menu dedicated di Workspace Home untuk meninjau log aktivitas, dilengkapi pencarian filter berdasarkan action (*LOGIN, SERVER_ACTION, DEPLOY, BACKUP, dll.*), resource type, status, dan dialog detail metadata audit dengan tampilan JSON terformat & tersanitasi.
      - **RBAC Guard**: Tombol/Menu Audit Log hanya ditampilkan dan dapat diakses oleh user ber-role `OWNER` / `ADMIN`.
  - **Step 15: DevOps Standalone Agent (TERBARU)**:
    - **Tujuan**: Implementasi lightweight Linux agent daemon dengan outbound-only connection, strict operation allowlist, dan dual-transport abstraction (`SSHProvider` & `AgentProvider`) tanpa mengubah stabilitas server existing.
    - **Arsitektur Transport**:
      ```text
      Flutter Mobile App -> FastAPI Backend (Control Plane)
                                  |
                                  | Outbound WebSocket / TLS
                                  v
                            DevOps Agent (Execution Plane)
                                  ├── Linux System Metrics
                                  ├── Systemd Service Management
                                  ├── Docker Container Engine
                                  ├── PostgreSQL Database Tools
                                  └── Filesystem Backup Engine
      ```
    - **Fitur Utama**:
      - **One-Time Enrollment Token**: Token pendaftaran short-lived (15 menit), single-use, dan disimpan dalam bentuk hash SHA-256 (bukan plaintext).
      - **Outbound-Only Connection**: Agent yang menghubungkan diri keluar ke Backend (`/api/v1/agent/ws`), sehingga server target tidak perlu membuka port inbound SSH baru di firewall.
      - **Predefined Operation Allowlist**: Agent hanya mengeksekusi operasi yang terdaftar resmi. Sama sekali tidak menerima arbitrary command string atau remote terminal shell.
      - **Replay Protection & Timeout**: Setiap job memiliki UUID, expiration ISO datetime, timeout, dan random nonce untuk mencegah replay attack.
      - **Dual Transport Provider Abstraction**: `ProviderFactory` mengarahkan eksekusi ke `AgentProvider` atau `SSHProvider` secara transparan berdasarkan `server.connection_type`. Server mode `AGENT` yang offline tidak akan secara diam-diam fallback ke SSH tanpa konfigurasi eksplisit.
      - **Flutter Mobile**: Section dedicated DevOps Agent di Server Detail menampilkan status online/offline, versi agent, waktu heartbeat, checklist capabilities terdaftar, serta dialog one-time setup command dengan tombol salin cepat.

---

## 4. Menjalankan & Menguji Aplikasi

### Uji Backend
```bash
docker compose up -d --build
docker compose exec backend pytest -v
```

### Uji Flutter Mobile
```bash
cd mobile
flutter pub get
flutter analyze
flutter test
```




