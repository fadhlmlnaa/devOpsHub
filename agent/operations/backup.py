import hashlib
import os
import subprocess
import tarfile
from datetime import datetime, timezone
from typing import Dict, Any, List


def calculate_sha256(file_path: str) -> str:
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            sha256.update(chunk)
    return sha256.hexdigest()


def execute_backup(payload: Dict[str, Any]) -> Dict[str, Any]:
    action = payload.get("action", "execute")

    if action == "validate":
        dest = payload.get("destination_path", "")
        valid = os.path.exists(dest) or os.path.exists(os.path.dirname(os.path.abspath(dest)))
        return {"valid": valid, "message": "Destination valid." if valid else "Destination path tidak ditemukan."}

    if action == "verify":
        file_path = payload.get("file_path", "")
        expected = payload.get("expected_checksum")
        exists = os.path.exists(file_path)
        if not exists:
            return {"verified": False, "file_exists": False, "message": "File backup tidak ditemukan pada filesystem."}
        calculated = calculate_sha256(file_path)
        verified = (calculated == expected) if expected else True
        return {
            "verified": verified,
            "file_exists": True,
            "calculated_checksum": calculated,
            "message": "Checksum cocok." if verified else "Checksum tidak cocok (file mungkin korup).",
        }

    # Execute Backup
    backup_type = payload.get("backup_type", "DIRECTORY")
    source_path = payload.get("source_path", "")
    destination_path = payload.get("destination_path", "/tmp/backups")
    os.makedirs(destination_path, exist_ok=True)

    timestamp_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    file_name = f"backup_{backup_type.lower()}_{timestamp_str}.tar.gz"
    target_file = os.path.join(destination_path, file_name)

    logs: List[Dict[str, Any]] = []
    logs.append({"level": "INFO", "message": f"Memulai backup {backup_type} dari {source_path}..."})

    try:
        if backup_type == "POSTGRESQL":
            db_name = payload.get("db_name", "postgres")
            db_user = payload.get("db_user", "postgres")
            sql_file = os.path.join(destination_path, f"{db_name}_{timestamp_str}.sql")
            proc = subprocess.run(["pg_dump", "-U", db_user, "-d", db_name, "-f", sql_file], capture_output=True, text=True)
            if proc.returncode != 0:
                return {"success": False, "status": "FAILED", "error_message": proc.stderr, "logs": logs}
            # Compress
            with tarfile.open(target_file, "w:gz") as tar:
                tar.add(sql_file, arcname=os.path.basename(sql_file))
            if os.path.exists(sql_file):
                os.remove(sql_file)
        else:
            with tarfile.open(target_file, "w:gz") as tar:
                tar.add(source_path, arcname=os.path.basename(source_path))

        size_bytes = os.path.getsize(target_file)
        checksum = calculate_sha256(target_file)
        logs.append({"level": "INFO", "message": f"Backup selesai: {file_name} ({size_bytes} bytes)."})

        return {
            "success": True,
            "status": "SUCCESS",
            "file_name": file_name,
            "file_path": target_file,
            "file_size_bytes": size_bytes,
            "checksum": checksum,
            "logs": logs,
        }
    except Exception as e:
        logs.append({"level": "ERROR", "message": str(e)})
        return {"success": False, "status": "FAILED", "error_message": str(e), "logs": logs}
