# DevOpsHub — Production Deployment Guide

Panduan ini mendokumentasikan prosedur instalasi dan deployment **DevOpsHub** pada production server Linux (Ubuntu 20.04/22.04/Debian/RHEL).

---

## 1. Prerequisites Server

* **OS**: Linux x86_64 atau ARM64
* **Hardware Rekomendasi**: Minimal 2 vCPU, 4GB RAM, 40GB SSD
* **Software Terpasang**:
  * Docker Engine (>= 24.0)
  * Docker Compose (>= 2.20)
  * Git & OpenSSL

---

## 2. Langkah-Langkah Deployment

### Langkah 1: Clone Repositori
```bash
git clone https://github.com/fadhlmlnaa/devOpsHub.git /opt/devopshub
cd /opt/devopshub
```

### Langkah 2: Konfigurasi Environment File
Salin template `.env.example` ke `.env`:
```bash
cp .env.example .env
```

Generate secret keys yang aman dan isi ke dalam `.env`:
```bash
# 1. JWT Secret Key (32 bytes hex)
openssl rand -hex 32

# 2. Credential Encryption Key (Fernet 32 url-safe base64 bytes)
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# 3. Agent HMAC Secret Key
openssl rand -hex 32

# 4. Password Database PostgreSQL
openssl rand -base64 24
```

Edit `.env` dengan nilai yang telah di-generate di atas:
```ini
APP_ENV=production
DATABASE_NAME=devops
DATABASE_USER=devops_admin
DATABASE_PASSWORD=<PASSWORD_DB_YANG_DIGENERATE>
JWT_SECRET_KEY=<JWT_KEY_YANG_DIGENERATE>
CREDENTIAL_ENCRYPTION_KEY=<FERNET_KEY_YANG_DIGENERATE>
AGENT_SECRET_KEY=<AGENT_KEY_YANG_DIGENERATE>
CORS_ALLOWED_ORIGINS=https://app.domainanda.com,https://api.domainanda.com
WEB_CONCURRENCY=4
```

### Langkah 3: Setup SSL / TLS Certificate (Let's Encrypt Certbot)
Siapkan sertifikat TLS/SSL untuk domain kamu dan letakkan di folder `./deploy/nginx/ssl/`:
```bash
mkdir -p ./deploy/nginx/ssl

# Contoh menggunakan Certbot standalone:
certbot certonly --standalone -d api.domainanda.com

# Hubungkan atau salin fullchain dan privkey:
cp /etc/letsencrypt/live/api.domainanda.com/fullchain.pem ./deploy/nginx/ssl/fullchain.pem
cp /etc/letsencrypt/live/api.domainanda.com/privkey.pem ./deploy/nginx/ssl/privkey.pem
```

### Langkah 4: Jalankan Container Production
```bash
docker compose -f docker-compose.prod.yml up -d --build
```

### Langkah 5: Jalankan Database Migrations (Alembic)
Migration otomatis dijalankan saat container `api` start, namun kamu dapat memverifikasi manual dengan:
```bash
docker compose -f docker-compose.prod.yml exec api alembic upgrade head
```

### Langkah 6: Jalankan Automated Smoke Test
```bash
python3 ./scripts/smoke_test.py https://api.domainanda.com
```

---

## 3. Zero-Downtime Update / Deployment Pipeline

Untuk melakukan update aplikasi ke versi baru:
```bash
# 1. Tarik pembaruan kode
git pull origin main

# 2. Buat backup database sebelum perubahan
./scripts/backup_db.sh

# 3. Rebuild dan restart service tanpa mematikan data volume
docker compose -f docker-compose.prod.yml up -d --build

# 4. Verifikasi status kesehatan
curl -s -i https://api.domainanda.com/api/v1/health/ready
```
