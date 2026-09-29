# DevOps Standalone Agent Documentation

## 1. Arsitektur & Filosofi Desain

DevOpsHub Agent adalah lightweight daemon yang di-install pada server Linux target untuk mengeksekusi operasi manajemen server tanpa membutuhkan inbound open port (seperti port SSH 22).

```text
Flutter Mobile App
      |
      | HTTPS
      v
FastAPI Backend (Control Plane)
      |
      | Outbound TLS / WebSocket (/api/v1/agent/ws)
      v
DevOps Agent (Execution Plane)
      |
      +--> Linux Kernel & Metrics (psutil / procfs)
      +--> systemd (Controlled systemctl)
      +--> Docker Engine (Docker SDK / API)
      +--> PostgreSQL (pg_dump / psql)
      +--> Filesystem (Controlled backup)
```

### Prinsip Utama:
1. **Control Plane vs Execution Plane**: Backend mengontrol otorisasi, RBAC, audit log, dan status. Agent murni bertindak sebagai pelaksana (execution plane).
2. **Outbound-Only Transport**: Agent yang melakukan inisiasi koneksi keluar (*outbound*) ke Backend via WebSocket / HTTPS. Server target tidak perlu membuka port inbound baru di firewall.
3. **Strict Operation Allowlist**: Agent HANYA mengeksekusi operasi yang terdaftar secara eksplisit.
4. **NO Arbitrary Shell Execution**: Backend/Mobile **DILARANG** mengirim string shell sembarang ke Agent.
5. **Least Privilege**: Agent tidak memerlukan root penuh (`NOPASSWD: ALL` dilarang).

---

## 2. Enrollment Lifecycle & Keamanan Token

```text
Admin / Owner di Flutter App
           |
           v
POST /api/v1/workspaces/{ws_id}/servers/{srv_id}/agent/enrollment
           |
           v
One-Time Enrollment Token (Hashed with SHA-256 in DB, TTL 15 menit)
           |
           v
Admin menjalankan installer di Linux Server target:
python -m agent.main enroll --server https://backend.example.com --token doh_enroll_...
           |
           v
Agent Handshake -> Backend memvalidasi token, mencatat identitas, & token di-hanguskan (used_at)
           |
           v
Backend menerbitkan Kredensial Permanen Agent (agent_id & agent_token_hash)
           |
           v
Agent menghubungkan WebSocket Outbound & Mengirim Heartbeat Periodik
```

---

## 3. Instalasi & Systemd Service

### Persyaratan:
- Linux (Ubuntu 20.04+, Debian 11+, RHEL 8+, Alpine 3.18+)
- Python 3.9+
- `systemd` dan `docker` (opsional jika mengelola container)

### Langkah Instalasi:
1. Salin direktori `agent/` ke `/opt/devops-agent`.
2. Buat virtual environment dan install dependencies:
   ```bash
   python3 -m venv /opt/devops-agent/venv
   /opt/devops-agent/venv/bin/pip install -r /opt/devops-agent/requirements.txt
   ```
3. Daftarkan agent menggunakan enrollment token yang di-generate dari dashboard/app:
   ```bash
   /opt/devops-agent/venv/bin/python -m agent.main enroll \
     --server https://api.devopshub.example.com \
     --token doh_enroll_YOUR_TOKEN_HERE \
     --config /etc/devops-agent/config.json
   ```
4. Pasang Systemd Unit:
   ```bash
   sudo cp agent/systemd/devops-agent.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable --now devops-agent.service
   ```
5. Pasang Sudoers Minimal (Least Privilege):
   ```bash
   sudo cp agent/systemd/devops-agent.sudoers /etc/sudoers.d/devops-agent
   sudo chmod 0440 /etc/sudoers.d/devops-agent
   ```

---

## 4. Operation Allowlist

Daftar operasi resmi yang didukung oleh Agent:

| Operation Key | Keterangan | Input Parameter |
| :--- | :--- | :--- |
| `GET_SYSTEM_METRICS` | Mengambil telemetry CPU, RAM, Disk, Load, Network | `{}` |
| `GET_SERVER_INFO` | Informasi OS, Kernel, Hostname, Uptime | `{}` |
| `GET_SERVICE_STATUS` | Status unit systemd | `{"service_name": "nginx.service"}` |
| `START_SERVICE` | Memulai unit systemd | `{"service_name": "nginx.service"}` |
| `STOP_SERVICE` | Menghentikan unit systemd | `{"service_name": "nginx.service"}` |
| `RESTART_SERVICE` | Me-restart unit systemd | `{"service_name": "nginx.service"}` |
| `RELOAD_SERVICE` | Reload konfigurasi unit systemd | `{"service_name": "nginx.service"}` |
| `GET_SERVICE_LOGS` | Mengambil journal logs service | `{"service_name": "nginx.service", "lines": 50}` |
| `GET_DOCKER_INFO` | Status instalasi & versi Docker | `{}` |
| `LIST_DOCKER_CONTAINERS`| Daftar container aktif & semua status | `{"all": true}` |
| `GET_DOCKER_CONTAINER` | Detail container | `{"container_id": "abc123"}` |
| `START_DOCKER_CONTAINER`| Start container | `{"container_id": "abc123"}` |
| `STOP_DOCKER_CONTAINER` | Stop container | `{"container_id": "abc123"}` |
| `RESTART_DOCKER_CONTAINER`| Restart container | `{"container_id": "abc123"}` |
| `GET_DOCKER_LOGS` | Log output container | `{"container_id": "abc123", "lines": 100}` |
| `DEPLOY` | Menjalankan deployment hook terisolasi | `{"application_name": "...", ...}` |
| `BACKUP` | Menjalankan pg_dump / backup terisolasi | `{"backup_type": "POSTGRESQL", ...}` |

Setiap request yang mengirim operasi di luar allowlist di atas akan langsung ditolak dengan error `UNKNOWN_OPERATION / Operation not allowed`.

---

## 5. Replay Protection, Nonce & Timeout

Setiap job execution memiliki:
- **`job_id` (UUID)**: Identifier unik job.
- **`nonce` (Random Token)**: Agent memvalidasi bahwa setiap nonce hanya dieksekusi 1 kali (Replay protection).
- **`expires_at` (ISO Datetime)**: Job yang tiba melebihi waktu kedaluwarsa akan ditolak (`EXPIRED_JOB`).
- **`timeout_seconds`**: Default 30 detik untuk mencegah proses menggantung.

---

## 6. Provider Abstraction & Dual Transport

DevOpsHub mendukung mode koneksi **`SSH`** dan **`AGENT`** secara berdampingan tanpa merusak konfigurasi server existing.

```text
ProviderFactory
  ├── get_service_provider()    --> SSHSystemdProvider / AgentSystemdProvider
  ├── get_docker_provider()     --> SSHDockerProvider / AgentDockerProvider
  ├── get_deployment_provider() --> SSHDeploymentProvider / AgentDeploymentProvider
  ├── get_backup_provider()     --> SSHBackupProvider / AgentBackupProvider
  └── get_log_provider()        --> SSHJournalLogProvider / AgentLogProvider
```

Jika server berada dalam mode `AGENT` dan Agent offline, sistem **TIDAK AKAN** secara diam-diam beralih ke SSH tanpa konfigurasi eksplisit admin demi menjaga konsistensi security boundary.

---

## 7. Revoke & Disable

- **Disable Agent**: Menonaktifkan sementara koneksi Agent tanpa menghapus data server.
- **Revoke Agent**: Menghapus hash kredensial Agent dari database dan mengembalikan mode koneksi server menjadi `SSH`.
