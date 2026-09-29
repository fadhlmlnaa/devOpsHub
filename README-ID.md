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
  (Placeholder Environment & Server untuk Step berikutnya)
```

---

## 3. Fitur Keamanan & Best Practices Step 05

1. **Secure Storage**: Access token dan refresh token disimpan di KeyStore (Android) dan Keychain (iOS) melalui `flutter_secure_storage`. Password tidak pernah disimpan di device.
2. **Single-Flight Refresh Token Lock**: Jika terjadi beberapa request bersamaan saat access token kadaluarsa (401), hanya 1 request refresh yang dipicu ke backend. Request lainnya menunggu completer dan otomatis mengulang request dengan token baru.
3. **No Sensitive Logging**: Token, password, dan exception traceback tidak dicetak di console log.
4. **Desain Visual & Tipografi**: Menggunakan font **Plus Jakarta Sans** (`google_fonts`) dan tema gelap bernuansa **Deep Dark Teal** (`#071E1B`, `#0B2925`) dengan aksen **Electric Cyan** (`#00D2FF`) sesuai logo DevOpsHub.

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
