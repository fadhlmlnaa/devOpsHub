# DevOpsHub — Enterprise Production Architecture

DevOpsHub adalah **Multi-Tenant DevOps Mobile Management Platform** yang dirancang untuk mengelola ribuan server Linux, kontainer Docker, layanan systemd, deployment pipeline, dan backup terjadwal secara real-time langsung dari perangkat mobile Android/iOS.

Prinsip Utama:
```text
Install once. Configure anywhere.
```

---

## 1. High-Level Architecture Diagram

```text
                            ┌────────────────────────┐
                            │      Flutter App       │
                            │ (Mobile Android / iOS) │
                            └───────────┬────────────┘
                                        │
                                      HTTPS
                                        │
                                        ▼
                            ┌────────────────────────┐
                            │     Reverse Proxy      │
                            │   (Nginx / HAProxy)    │
                            └───────────┬────────────┘
                                        │
                          ┌─────────────┴─────────────┐
                          │                           │
                        HTTP                         WSS
                          │                           │
                          ▼                           ▼
            ┌───────────────────────────┐   ┌───────────────────────────┐
            │       FastAPI API         │   │   WebSocket Dispatcher    │
            │      Control Plane        │   │    (Agent Ingestion)      │
            └─────────────┬─────────────┘   └─────────────┬─────────────┘
                          │                               │
            ┌─────────────┴─────────────┐                 │
            │                           │                 │
            ▼                           ▼                 ▼
   ┌─────────────────┐         ┌─────────────────┐  ┌───────────┐
   │   PostgreSQL    │         │      Redis      │  │  Worker   │
   │  (Primary DB)   │         │ (Queue & Cache) │  │  Daemon   │
   └─────────────────┘         └─────────────────┘  └───────────┘
                                        │
                                        ▼
                            DevOps Management Layer
                                        │
                   ┌────────────────────┴────────────────────┐
                   │                                         │
                   ▼                                         ▼
            SSH Connection                             DevOps Agent
              (Port 22)                               (Outbound TLS)
                   │                                         │
                   ▼                                         ▼
           Target Servers                             Target Servers
        (Traditional Linux)                        (Zero Inbound Port)
```

---

## 2. Core Components

### 2.1 Control Plane (FastAPI API & WebSocket Dispatcher)
* **Framework**: FastAPI (Python 3.11 ASGI), Uvicorn / Gunicorn Concurrency Workers.
* **Tanggung Jawab**:
  * Autentikasi JWT dengan refresh token rotation.
  * Multi-tenant workspace isolation & Role-Based Access Control (RBAC).
  * REST API untuk Server, Environment, Monitoring, Services, Docker, Deployment, Backup, dan Alerts.
  * Real-time WebSocket bidirectional connection hub untuk komunikasi dengan DevOps Standalone Agents.
  * Automated Audit Logging pada setiap operasi sensitif.

### 2.2 Relational Database (PostgreSQL 16)
* **Tanggung Jawab**:
  * Persistent storage untuk Users, Workspaces, Environments, Servers, Credentials (encrypted), Agent tokens, Alert rules, Deployment configs, Backup metadata, dan Audit logs.
  * Single source of truth dengan foreign key cascades, unique constraints, dan optimized index pada `workspace_id`, `environment_id`, `server_id`, `created_at`.
  * Managed via Alembic schema migrations (`alembic upgrade head`).

### 2.3 Caching & In-Memory Coordination (Redis 7)
* **Tanggung Jawab**:
  * Temporary session store & fast rate limiting tracking.
  * Background job coordination and messaging between API and background workers.
  * Eviction policy: `allkeys-lru` dengan fixed memory limit (256MB).

### 2.4 Standalone Background Worker
* **Tanggung Jawab**:
  * Evaluasi periodik alert rules (CPU, Memory, Disk, Load average, Service state, Docker health).
  * Eksekusi notifikasi batch dan retention cleanup log.
  * Menangani task berat di luar event loop request FastAPI.

### 2.5 Dual-Transport Management Layer (SSH & Agent)
* **SSH Provider**:
  * Menggunakan AsyncSSH untuk remote server tradisional.
  * Enkripsi kredensial simetris (Fernet 256-bit AES) in-memory.
* **Agent Provider**:
  * Outbound TLS/WebSocket connection dari target Linux ke control plane.
  * Zero inbound ports, strict allowlist operations, nonce-guarded replay protection.

---

## 3. Multi-Tenant Logical Model

```text
Company / Organization
   └── Workspace (Multi-Tenant Boundary)
        ├── Roles: OWNER, ADMIN, DEVELOPER, VIEWER
        ├── Environments
        │    ├── DEV
        │    ├── STAGING
        │    └── PROD (Protected: Require explicit confirmation)
        ├── Servers
        │    ├── Connection Type: SSH / AGENT
        │    ├── Systemd Services
        │    ├── Docker Containers & Compose Projects
        │    ├── Deployment Pipelines
        │    └── Backup Schedules
        ├── Alert Rules & Notification Channels
        └── Audit Logs (Tamper-evident log trail)
```
