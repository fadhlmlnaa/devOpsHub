# DevOps Mobile Platform

Platform DevOps Mobile modular dan agnostik perusahaan yang dirancang untuk memberikan akses mobile bagi developer dan tim operasional ke infrastruktur serta otomasi DevOps.

[🇬🇧 Read English Documentation](file:///Users/fadhilmaulana/MyProject/DevOpsHub/README.md) | [🧪 Panduan Testing Mandiri (README-TEST-ID.md)](file:///Users/fadhilmaulana/MyProject/DevOpsHub/README-TEST-ID.md)

> **Status Saat Ini**: **Step 02 — Database & Core Domain Models (Database & Model Domain Utama)**. Skema domain inti, model SQLAlchemy 2.x, migrasi Alembic, schema Pydantic, dan pengujian model telah diimplementasikan. Fitur autentikasi (JWT/Login), manajemen SSH, monitoring, Docker, dan agen DevOps belum diimplementasikan pada tahap ini.

---

## 1. Ikhtisar Proyek

DevOps Mobile Platform menerapkan arsitektur terpisah (*decoupled*) yang memisahkan antara antarmuka mobile lintas platform, REST API backend berkinerja tinggi, dan database relasional yang andal.

---

## 2. Arsitektur & Hirarki Domain

```text
Aplikasi Mobile Flutter
       |
       | HTTP / REST (/api/v1)
       v
 FastAPI Backend
       |
       | Connection Pool (SQLAlchemy 2.x / Alembic)
       v
   PostgreSQL
```

### Hirarki Domain

```text
User (UUID PK, UTC timestamps)
  └── memberships (WorkspaceMember: OWNER, ADMIN, DEVELOPER, VIEWER)
        └── Workspace (UUID PK, multi-tenant capable, company-agnostic)
              ├── Environments (development, staging, production, custom)
              │     └── Servers (hostname, IP, port SSH, OS)
              └── Servers (terikat pada workspace + environment)
```

---

## 3. Kebutuhan Sistem

- **Docker & Docker Compose**: Docker 20.10+ / Compose v2+
- **Python**: 3.10+ (untuk pengembangan backend lokal)
- **Flutter SDK**: 3.x+ (untuk pengembangan aplikasi mobile)
- **PostgreSQL**: 15+ (jika dijalankan tanpa Docker)

---

## 4. Konfigurasi Awal (Setup Lokal)

1. **Clone repositori**:
   ```bash
   git clone <repository_url>
   cd DevOpsHub
   ```

2. **Siapkan variabel lingkungan (*environment variables*)**:
   ```bash
   cp .env.example .env
   ```

---

## 5. Menjalankan dengan Docker Compose (Direkomendasikan)

Jalankan layanan PostgreSQL dan backend FastAPI secara bersamaan:

```bash
docker compose up -d --build
```

Periksa status kontainer yang sedang berjalan:
```bash
docker compose ps
```

Jalankan migrasi database (Alembic):
```bash
docker compose exec backend alembic upgrade head
```

Jalankan pengujian unit/model (Pytest):
```bash
docker compose exec backend pytest
```

(Opsional) Masukkan data dummy pengembangan (*seed data*):
```bash
docker compose exec backend python -m app.db.seed
```

Akses layanan:
- **FastAPI Health Check**: [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)
- **Dokumentasi Interaktif Swagger**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Dokumentasi ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

Menghentikan layanan:
```bash
docker compose down
```

---

## 6. Menjalankan Layanan Secara Terpisah

### Menjalankan PostgreSQL Saja

Menggunakan Docker:
```bash
docker compose up -d postgres
```

### Menjalankan Backend Secara Manual

1. Masuk ke direktori backend:
   ```bash
   cd backend
   ```
2. Buat dan aktifkan *virtual environment* Python:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
3. Pasang dependensi:
   ```bash
   pip install -r requirements.txt
   ```
4. Jalankan migrasi:
   ```bash
   alembic upgrade head
   ```
5. Jalankan pengujian:
   ```bash
   pytest
   ```
6. Jalankan backend:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

---

## 7. Menjalankan Aplikasi Mobile Flutter

1. Masuk ke direktori mobile:
   ```bash
   cd mobile
   ```
2. Unduh dependensi Flutter:
   ```bash
   flutter pub get
   ```
3. Jalankan pengujian widget (*widget test*):
   ```bash
   flutter test
   ```
4. Jalankan aplikasi:
   ```bash
   flutter run
   ```

---

## 8. Variabel Lingkungan (*Environment Variables*)

| Variabel | Deskripsi | Nilai Default |
| :--- | :--- | :--- |
| `DATABASE_HOST` | Host database PostgreSQL | `localhost` / `postgres` (docker) |
| `DATABASE_PORT` | Port untuk PostgreSQL | `5432` |
| `DATABASE_NAME` | Nama database | `devops` |
| `DATABASE_USER` | Username database | `devops` |
| `DATABASE_PASSWORD` | Password database | `change_me` |
| `BACKEND_PORT` | Port yang diekspos oleh FastAPI | `8000` |

---

## 9. Cakupan Proyek Saat Ini

- [x] **Step 01 — Fondasi Proyek**: Struktur terpisah, Docker Compose, Flutter skeleton, `/api/v1/health`.
- [x] **Step 02 — Database & Core Domain Models**:
  - [x] Model deklaratif modern SQLAlchemy 2.x (`User`, `Workspace`, `WorkspaceMember`, `Environment`, `Server`).
  - [x] Primary key berbasis UUID & penanganan timestamp UTC yang konsisten.
  - [x] Database constraint (`UNIQUE` pada email, `(workspace_id, user_id)`, `(workspace_id, key)`).
  - [x] Migrasi Alembic (`001_initial_schema.py`) dengan verifikasi upgrade dan downgrade.
  - [x] Test suite lengkap (11 tes unit & integrasi model berhasil 100%).
  - [x] Skrip seeder data pengembangan (`app.db.seed`).
- [ ] *Tahap Berikutnya (Step 03+): Autentikasi (JWT/Login), registrasi user, manajemen server & SSH, monitoring, integrasi agen DevOps.*
