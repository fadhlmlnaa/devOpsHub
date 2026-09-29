#!/usr/bin/env bash
# ==============================================================================
# DevOpsHub — Production PostgreSQL Backup Automation Script
# ==============================================================================
set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-./backups/db}"
CONTAINER_NAME="${CONTAINER_NAME:-devopshub_postgres}"
# Fallback to local dev container name if prod is not running
if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    CONTAINER_NAME="devops_postgres"
fi

DB_USER="${POSTGRES_USER:-devops}"
DB_NAME="${POSTGRES_DB:-devops}"
TIMESTAMP=$(date -u +"%Y%m%d_%H%M%S")
FILENAME="devopshub_${DB_NAME}_backup_${TIMESTAMP}.dump"
FILEPATH="${BACKUP_DIR}/${FILENAME}"
CHECKSUM_FILE="${FILEPATH}.sha256"

mkdir -p "${BACKUP_DIR}"

echo "=========================================================="
echo " Starting DevOpsHub Database Backup: ${TIMESTAMP}"
echo " Container: ${CONTAINER_NAME} | Database: ${DB_NAME}"
echo "=========================================================="

# 1. Execute pg_dump directly inside container (compressed custom format)
docker exec "${CONTAINER_NAME}" pg_dump -U "${DB_USER}" -d "${DB_NAME}" -F c -b -v > "${FILEPATH}"

# 2. Compute SHA-256 Checksum
if command -v shasum >/dev/null 2>&1; then
    shasum -a 256 "${FILEPATH}" > "${CHECKSUM_FILE}"
elif command -v sha256sum >/dev/null 2>&1; then
    sha256sum "${FILEPATH}" > "${CHECKSUM_FILE}"
fi

FILE_SIZE=$(du -h "${FILEPATH}" | cut -f1)
echo " [OK] Backup berhasil dibuat: ${FILEPATH} (${FILE_SIZE})"
echo " [OK] Checksum SHA256: $(cat "${CHECKSUM_FILE}")"

# 3. Retention Cleanup (Remove backups older than 30 days)
echo " Membersihkan backup lama (> 30 hari)..."
find "${BACKUP_DIR}" -type f -name "devopshub_*_backup_*.dump*" -mtime +30 -exec rm -f {} +

echo " Backup selesai secara aman."
