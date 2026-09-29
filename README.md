# DevOps Mobile Platform

A modular, company-agnostic DevOps Mobile Platform designed to provide developers and operations teams with mobile access to DevOps infrastructure and automation.

[🇮🇩 Baca Dokumentasi Bahasa Indonesia](file:///Users/fadhilmaulana/MyProject/DevOpsHub/README-ID.md) | [🧪 Panduan Testing Mandiri (README-TEST-ID.md)](file:///Users/fadhilmaulana/MyProject/DevOpsHub/README-TEST-ID.md)

> **Current Status**: **Step 05 — Flutter Foundation, Authentication & Workspace Selection**. Complete Flutter mobile client built with GetX, Dio API client, encrypted secure storage (`flutter_secure_storage`), token refresh rotation lock, Plus Jakarta Sans typography, and custom base widgets styled to match the DevOpsHub brand teal & electric cyan palette. 15 Flutter tests and 34 backend tests passing with 0 lint warnings.

---

## 1. Project Overview

The DevOps Mobile Platform establishes a decoupled architecture separating a cross-platform mobile interface, a high-performance REST backend API, and a robust relational database.

---

## 2. Architecture & Tech Stack

```text
Flutter Mobile Client (GetX, Dio, SecureStorage, Plus Jakarta Sans)
       |
       | HTTP / REST (JWT Bearer Auth /api/v1)
       v
 FastAPI Backend (Python 3.11, Argon2, JWT Access/Refresh Rotation)
       |
       | Connection Pool (SQLAlchemy 2.x / Alembic)
       v
   PostgreSQL 16
```

### Domain Hierarchy

```text
User (UUID PK, Argon2 password hash, UTC timestamps)
  ├── refresh_tokens (SHA-256 hashed, revocable, rotatable)
  └── memberships (WorkspaceMember: OWNER, ADMIN, DEVELOPER, VIEWER)
        └── Workspace (UUID PK, multi-tenant capable, company-agnostic)
              ├── Environments (development, staging, production, custom)
              │     └── Servers (hostname, IP, SSH port, OS)
              └── Servers (scoped to workspace + environment)
```

---

## 3. Flutter Client Architecture (Step 05)

```text
mobile/
└── lib/
    ├── main.dart
    ├── app/
    │   ├── routes/ (AppPages, AppRoutes)
    │   └── theme/  (AppTheme, AppColors)
    ├── core/
    │   ├── constants/ (AppConstants)
    │   ├── network/   (ApiClient, ApiException)
    │   ├── storage/   (SecureStorageService)
    │   └── widgets/   (AppButton, AppTextField, AppAppBar, AppBottomSheet, AppCard, AppStatusBadge)
    ├── data/
    │   ├── models/    (UserModel, AuthTokenModel, WorkspaceModel, WorkspaceMemberModel)
    │   └── services/  (AuthService, WorkspaceService)
    ├── modules/
    │   ├── splash/    (SplashController, SplashView)
    │   ├── auth/      (AuthController, LoginView, RegisterView)
    │   └── workspace/ (WorkspaceController, WorkspaceListView, WorkspaceHomeView, CreateWorkspaceSheet)
    └── bindings/      (InitialBinding, AuthBinding, WorkspaceBinding)
```

---

## 4. API Endpoints

### Authentication
- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/refresh`
- `POST /api/v1/auth/logout`
- `GET /api/v1/auth/me` *(Protected)*

### Workspaces & Members *(All Protected)*
- `POST /api/v1/workspaces`: Create workspace (creator becomes OWNER)
- `GET /api/v1/workspaces`: List user's workspaces
- `GET /api/v1/workspaces/{workspace_id}`: Workspace detail
- `PATCH /api/v1/workspaces/{workspace_id}`: Update workspace (OWNER, ADMIN)
- `GET /api/v1/workspaces/{workspace_id}/members`: List workspace members
- `POST /api/v1/workspaces/{workspace_id}/members`: Add new member
- `PATCH /api/v1/workspaces/{workspace_id}/members/{user_id}`: Update member role
- `DELETE /api/v1/workspaces/{workspace_id}/members/{user_id}`: Remove member
- `DELETE /api/v1/workspaces/{workspace_id}/members/me`: Self leave workspace

---

## 5. Running & Testing

### Backend
```bash
# Build & Start services
docker compose up -d --build

# Run backend test suite (34 tests)
docker compose exec backend pytest -v
```

### Mobile
```bash
cd mobile

# Install dependencies
flutter pub get

# Code analysis
flutter analyze

# Run mobile test suite (15 tests)
flutter test
```

---

## 6. Current Project Scope

- [x] **Step 01 — Project Foundation**: Decoupled structure, Docker Compose, Flutter skeleton, `/api/v1/health`.
- [x] **Step 02 — Database & Core Domain Models**: SQLAlchemy 2.x models, UUID primary keys, UTC timestamps, Alembic migrations.
- [x] **Step 03 — Authentication & JWT**: Argon2 password hashing, JWT access token, revocable refresh tokens with rotation, `/auth/me`.
- [x] **Step 04 — Authorization & Workspace API**: Centralized `RequireWorkspaceRole`, Workspace CRUD, Member management with granular role constraints, Anti-IDOR protection, 34 backend tests.
- [x] **Step 05 — Flutter Foundation & Workspace Selection**: GetX routing & DI, Dio API client with single-flight refresh lock, encrypted secure storage, Plus Jakarta Sans, brand base widgets, Splash, Login, Register, Workspace List, Workspace Create modal, Workspace Home placeholder, 15 tests.
- [ ] *Pending Step 06+: Environment Management API, Server Management API, SSH Execution, Server Monitoring.*
