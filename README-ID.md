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
