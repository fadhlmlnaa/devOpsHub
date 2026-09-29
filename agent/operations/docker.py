import json
import re
import shutil
import subprocess
from typing import Dict, Any, List

CONTAINER_ID_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+$")


def validate_container_id(cid: str) -> str:
    clean = cid.strip()
    if not CONTAINER_ID_PATTERN.match(clean):
        raise ValueError(f"Container ID '{cid}' tidak valid.")
    return clean


def execute_get_docker_info(payload: Dict[str, Any]) -> Dict[str, Any]:
    docker_bin = shutil.which("docker")
    if not docker_bin:
        return {"installed": False, "running": False, "state": "NOT_INSTALLED"}

    proc = subprocess.run(["docker", "info", "--format", "{{json .}}"], capture_output=True, text=True, timeout=10)
    if proc.returncode != 0:
        return {"installed": True, "running": False, "state": "STOPPED", "error": proc.stderr}

    version_proc = subprocess.run(["docker", "--version"], capture_output=True, text=True, timeout=5)
    version = version_proc.stdout.strip() if version_proc.returncode == 0 else "Docker"

    return {"installed": True, "running": True, "version": version, "state": "RUNNING"}


def execute_list_docker_containers(payload: Dict[str, Any]) -> Dict[str, Any]:
    state_filter = payload.get("state_filter", "running")
    cmd = ["docker", "ps", "--format", "{{json .}}", "--no-trunc"]
    if state_filter == "all":
        cmd.append("-a")

    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
    containers = []
    for line in proc.stdout.splitlines():
        if not line.strip():
            continue
        try:
            data = json.loads(line)
            containers.append({
                "id": data.get("ID", "")[:12],
                "name": data.get("Names", ""),
                "image": data.get("Image", ""),
                "status": data.get("Status", ""),
                "state": data.get("State", ""),
                "created_at": data.get("CreatedAt", ""),
                "ports": [p.strip() for p in data.get("Ports", "").split(",") if p.strip()],
            })
        except Exception:
            pass

    return {"containers": containers}


def execute_get_docker_container(payload: Dict[str, Any]) -> Dict[str, Any]:
    cid = validate_container_id(payload.get("container_id", ""))
    cmd = ["docker", "inspect", cid]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
    if proc.returncode != 0:
        return {"container": None}

    try:
        data = json.loads(proc.stdout)
        if not data:
            return {"container": None}
        c = data[0]
        state = c.get("State", {})
        config = c.get("Config", {})
        host_config = c.get("HostConfig", {})

        return {
            "container": {
                "id": c.get("Id", "")[:12],
                "name": c.get("Name", "").lstrip("/"),
                "image": config.get("Image", ""),
                "state": state.get("Status", "unknown"),
                "status": f"{state.get('Status')} since {state.get('StartedAt')}",
                "created_at": c.get("Created"),
                "started_at": state.get("StartedAt"),
                "restart_policy": host_config.get("RestartPolicy", {}).get("Name"),
            }
        }
    except Exception:
        return {"container": None}


def execute_container_action(action: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    cid = validate_container_id(payload.get("container_id", ""))
    allowed = {"start", "stop", "restart"}
    if action not in allowed:
        raise ValueError(f"Aksi '{action}' tidak valid.")

    cmd = ["docker", action, cid]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    success = proc.returncode == 0
    return {
        "success": success,
        "container": cid,
        "action": action,
        "current_state": "running" if action in ("start", "restart") and success else "stopped",
        "message": f"Docker {action} {cid} {'berhasil' if success else 'gagal: ' + proc.stderr}",
    }


def execute_start_docker_container(payload: Dict[str, Any]) -> Dict[str, Any]:
    return execute_container_action("start", payload)


def execute_stop_docker_container(payload: Dict[str, Any]) -> Dict[str, Any]:
    return execute_container_action("stop", payload)


def execute_restart_docker_container(payload: Dict[str, Any]) -> Dict[str, Any]:
    return execute_container_action("restart", payload)


def execute_get_docker_logs(payload: Dict[str, Any]) -> Dict[str, Any]:
    cid = validate_container_id(payload.get("container_id", ""))
    lines = int(payload.get("lines", 100))
    cmd = ["docker", "logs", "--tail", str(lines), cid]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
    entries = [{"message": l} for l in (proc.stdout + proc.stderr).splitlines() if l.strip()]
    return {"entries": entries, "lines_requested": lines, "lines_returned": len(entries)}
