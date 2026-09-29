# DevOps Mobile Platform

A modular, company-agnostic DevOps Mobile Platform designed to provide developers and operations teams with mobile access to DevOps infrastructure and automation.

[🇮🇩 Baca Dokumentasi Bahasa Indonesia](file:///Users/fadhilmaulana/MyProject/DevOpsHub/README-ID.md) | [🧪 Panduan Testing Mandiri (README-TEST-ID.md)](file:///Users/fadhilmaulana/MyProject/DevOpsHub/README-TEST-ID.md)

> **Current Status**: **Step 02 — Database & Core Domain Models**. Core domain schemas, SQLAlchemy 2.x models, Alembic migrations, Pydantic domain schemas, and tests are implemented. Authentication, SSH, monitoring, Docker management, and DevOps Agent are NOT part of this step.

---

## 1. Project Overview

The DevOps Mobile Platform establishes a decoupled architecture separating a cross-platform mobile interface, a high-performance REST backend API, and a robust relational database.

---

## 2. Architecture & Domain Hierarchy

```text
Flutter Mobile App
       |
       | HTTP / REST (/api/v1)
       v
 FastAPI Backend
       |
       | Connection Pool (SQLAlchemy 2.x / Alembic)
       v
   PostgreSQL
```

### Domain Hierarchy

```text
User (UUID PK, UTC timestamps)
  └── memberships (WorkspaceMember: OWNER, ADMIN, DEVELOPER, VIEWER)
        └── Workspace (UUID PK, multi-tenant capable, company-agnostic)
              ├── Environments (development, staging, production, custom)
              │     └── Servers (hostname, IP, SSH port, OS)
              └── Servers (scoped to workspace + environment)
```

---

## 3. Requirements

- **Docker & Docker Compose**: Docker 20.10+ / Compose v2+
- **Python**: 3.10+ (for local backend development)
- **Flutter SDK**: 3.x+ (for mobile app development)
- **PostgreSQL**: 15+ (if running without Docker)

---

## 4. Local Setup

1. **Clone the repository**:
   ```bash
   git clone <repository_url>
   cd DevOpsHub
   ```

2. **Configure environment variables**:
   ```bash
   cp .env.example .env
   ```

---

## 5. Running with Docker Compose (Recommended)

Start both PostgreSQL and the FastAPI backend services:

```bash
docker compose up -d --build
```

Verify running containers:
```bash
docker compose ps
```

Apply database migrations:
```bash
docker compose exec backend alembic upgrade head
```

Run test suite:
```bash
docker compose exec backend pytest
```

(Optional) Seed development data:
```bash
docker compose exec backend python -m app.db.seed
```

Access services:
- **FastAPI Health Check**: [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)
- **Interactive Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc Documentation**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

Stop services:
```bash
docker compose down
```

---

## 6. How to Start Services Individually

### Starting PostgreSQL Only

Using Docker:
```bash
docker compose up -d postgres
```

### Starting Backend Manually

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Create and activate a Python virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run migrations:
   ```bash
   alembic upgrade head
   ```
5. Run tests:
   ```bash
   pytest
   ```
6. Start the backend:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

---

## 7. How to Run Flutter Mobile App

1. Navigate to the mobile directory:
   ```bash
   cd mobile
   ```
2. Get dependencies:
   ```bash
   flutter pub get
   ```
3. Run widget tests:
   ```bash
   flutter test
   ```
4. Launch the application:
   ```bash
   flutter run
   ```

---

## 8. Environment Variables

| Variable | Description | Default |
| :--- | :--- | :--- |
| `DATABASE_HOST` | Hostname of the PostgreSQL database | `localhost` / `postgres` (docker) |
| `DATABASE_PORT` | Port for PostgreSQL | `5432` |
| `DATABASE_NAME` | Database name | `devops` |
| `DATABASE_USER` | Database username | `devops` |
| `DATABASE_PASSWORD` | Database password | `change_me` |
| `BACKEND_PORT` | Port exposed by FastAPI | `8000` |

---

## 9. Current Project Scope

- [x] **Step 01 — Project Foundation**: Decoupled structure, Docker Compose, Flutter skeleton, `/api/v1/health`.
- [x] **Step 02 — Database & Core Domain Models**:
  - [x] SQLAlchemy 2.x modern declarative models (`User`, `Workspace`, `WorkspaceMember`, `Environment`, `Server`).
  - [x] UUID primary keys and consistent UTC timestamps.
  - [x] Database constraints (`UNIQUE` on email, `(workspace_id, user_id)`, `(workspace_id, key)`).
  - [x] Alembic migration pipeline (`001_initial_schema.py`) with upgrade & rollback support.
  - [x] Comprehensive test suite (11 unit/integration model tests passed).
  - [x] Development data seeder (`app.db.seed`).
- [ ] *Pending Step 03+: Authentication (JWT/Tokens), user registration/login, SSH/Server management, monitoring, agent integration.*
