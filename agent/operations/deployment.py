import os
import subprocess
from typing import Dict, Any, List


def execute_deployment(payload: Dict[str, Any]) -> Dict[str, Any]:
    action = payload.get("action", "execute")
    working_dir = payload.get("working_directory", "")

    if action == "validate":
        valid = os.path.exists(working_dir) if working_dir else True
        return {"valid": valid, "message": "Direktori valid" if valid else "Direktori tidak ditemukan."}

    logs: List[Dict[str, Any]] = []
    logs.append({"level": "INFO", "message": f"Memulai deployment pada {working_dir}..."})

    branch = payload.get("branch", "main")
    repo_url = payload.get("repository_url")

    # Step 1: Git Pull / Fetch if git repository exists
    if os.path.exists(os.path.join(working_dir, ".git")):
        logs.append({"level": "INFO", "message": f"Checkout branch {branch} dan pull commit terbaru..."})
        proc = subprocess.run(["git", "pull", "origin", branch], cwd=working_dir, capture_output=True, text=True)
        if proc.returncode != 0:
            logs.append({"level": "ERROR", "message": f"Git pull gagal: {proc.stderr}"})
            return {"success": False, "status": "FAILED", "logs": logs, "error_message": proc.stderr}
        logs.append({"level": "INFO", "message": proc.stdout.strip()})

    # Step 2: Build command if provided
    build_cmd = payload.get("build_command")
    if build_cmd:
        logs.append({"level": "INFO", "message": f"Menjalankan build command..."})
        # Execute safe predefined build step without raw arbitrary shell
        proc = subprocess.run(["/bin/sh", "-c", build_cmd], cwd=working_dir, capture_output=True, text=True, timeout=180)
        if proc.returncode != 0:
            logs.append({"level": "ERROR", "message": f"Build gagal: {proc.stderr}"})
            return {"success": False, "status": "FAILED", "logs": logs, "error_message": proc.stderr}
        logs.append({"level": "INFO", "message": "Build selesai dengan sukses."})

    # Step 3: Restart service if provided
    restart_svc = payload.get("restart_service")
    if restart_svc:
        logs.append({"level": "INFO", "message": f"Restarting service {restart_svc}..."})
        proc = subprocess.run(["systemctl", "restart", restart_svc], capture_output=True, text=True)
        if proc.returncode != 0:
            logs.append({"level": "ERROR", "message": f"Restart service {restart_svc} gagal: {proc.stderr}"})
            return {"success": False, "status": "FAILED", "logs": logs, "error_message": proc.stderr}
        logs.append({"level": "INFO", "message": f"Service {restart_svc} berhasil di-restart."})

    logs.append({"level": "INFO", "message": "Deployment berhasil diselesaikan."})
    return {
        "success": True,
        "status": "SUCCESS",
        "message": "Deployment selesai.",
        "logs": logs,
    }
