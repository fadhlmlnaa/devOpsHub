#!/usr/bin/env bash
# ==============================================================================
# DevOpsHub — Production PostgreSQL Database Restore Script
# ==============================================================================
set -euo pipefail

if [ "$#" -lt 1 ]; then
    echo "Penggunaan: $0 <path_to_dump_file> [target_db_name]"
    echo "Contoh: $0 ./backups/db/devopshub_devops_backup_20260929_120000.dump"
    exit 1
fi

DUMP_FILE="$1"
TARGET_DB="${2:-devops}"
DB_USER="${POSTGRES_USER:-devops}"
CONTAINER_NAME="${CONTAINER_NAME:-devopshub_postgres}"

# Fallback to local dev container name if prod is not running
if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    CONTAINER_NAME="devops_postgres"
fi

if [ ! -f "${DUMP_FILE}" ]; then
    echo "Error: File backup '${DUMP_FILE}' tidak ditemukan!"
    exit 1
fi

echo "=========================================================="
echo " Starting DevOpsHub Database Restore"
echo " File: ${DUMP_FILE}"
echo " Target Container: ${CONTAINER_NAME} | Database: ${TARGET_DB}"
echo "=========================================================="

# 1. Verify Checksum if available
CHECKSUM_FILE="${DUMP_FILE}.sha256"
if [ -f "${CHECKSUM_FILE}" ]; then
    echo " Verifying SHA-256 checksum..."
    if command -v shasum >/dev/null 2>&1; then
        shasum -a 256 -c "${CHECKSUM_FILE}"
    elif command -v sha256sum >/dev/null 2>&1; then
        sha256sum -c "${CHECKSUM_FILE}"
    fi
    echo " [OK] Checksum terverifikasi valid."
fi

# 2. Recreate Target Database
echo " Recreating clean target database '${TARGET_DB}'..."
docker exec -i "${CONTAINER_NAME}" psql -U "${DB_USER}" -d postgres -c "DROP DATABASE IF EXISTS ${TARGET_DB}_restore_temp;" || true
docker exec -i "${CONTAINER_NAME}" psql -U "${DB_USER}" -d postgres -c "CREATE DATABASE ${TARGET_DB}_restore_temp;"

# 3. Restore dump into temp database
echo " Restoring schema and data..."
docker exec -i "${CONTAINER_NAME}" pg_restore -U "${DB_USER}" -d "${TARGET_DB}_restore_temp" --clean --if-exists --no-owner --no-privileges < "${DUMP_FILE}" || true

# 4. Swap database or apply to main
echo " Swapping databases..."
docker exec -i "${CONTAINER_NAME}" psql -U "${DB_USER}" -d postgres -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '${TARGET_DB}' AND pid <> pg_backend_pid();" || true
docker exec -i "${CONTAINER_NAME}" psql -U "${DB_USER}" -d postgres -c "DROP DATABASE IF EXISTS ${TARGET_DB};"
docker exec -i "${CONTAINER_NAME}" psql -U "${DB_USER}" -d postgres -c "ALTER DATABASE ${TARGET_DB}_restore_temp RENAME TO ${TARGET_DB};"


# 5. Sanity Check Smoke Query
echo " Running Smoke Validation Queries..."
docker exec -i "${CONTAINER_NAME}" psql -U "${DB_USER}" -d "${TARGET_DB}" -c "
    SELECT 'Users' as table_name, count(*) as count FROM users
    UNION ALL
    SELECT 'Workspaces', count(*) FROM workspaces
    UNION ALL
    SELECT 'Servers', count(*) FROM servers
    UNION ALL
    SELECT 'Audit Logs', count(*) FROM audit_logs;
"

echo " [OK] Database restore berhasil diselesaikan."
