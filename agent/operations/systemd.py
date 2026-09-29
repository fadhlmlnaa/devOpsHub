import re
import subprocess
from typing import Dict, Any, List

SERVICE_NAME_PATTERN = re.compile(r"^[A-Za-z0-9_.@:-]+\.service$")


def validate_service_name(name: str) -> str:
    cleaned = name.strip()
    if not SERVICE_NAME_PATTERN.match(cleaned):
        raise ValueError(f"Nama service '{name}' tidak valid. Harus berakhiran .service dan tanpa spasi.")
    return cleaned


def execute_get_service_status(payload: Dict[str, Any]) -> Dict[str, Any]:
    action = payload.get("action")
    if action == "list":
        limit = payload.get("limit", 100)
        state_filter = payload.get("state")
        cmd = ["systemctl", "list-units", "--type=service", "--all", "--no-pager", "--no-legend", "--plain"]
        if state_filter:
            cmd.extend(["--state", state_filter])

        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        services = []
        for line in proc.stdout.splitlines()[:limit]:
            parts = line.split(None, 4)
            if len(parts) >= 4 and parts[0].endswith(".service"):
                services.append({
                    "name": parts[0],
                    "load_state": parts[1],
                    "active_state": parts[2],
                    "sub_state": parts[3],
                    "description": parts[4] if len(parts) > 4 else None,
                })
        return {"services": services}

    service_name = validate_service_name(payload.get("service_name", ""))
    cmd = ["systemctl", "show", service_name, "--no-pager"]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

    props = {}
    for line in proc.stdout.splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            props[k.strip()] = v.strip()

    load_state = props.get("LoadState", "not-found")
    if load_state == "not-found":
        return {"service": None}

    main_pid = None
    try:
        pid_val = int(props.get("MainPID", "0"))
        if pid_val > 0:
            main_pid = pid_val
    except Exception:
        pass

    return {
        "service": {
            "name": service_name,
            "load_state": load_state,
            "active_state": props.get("ActiveState", "unknown"),
            "sub_state": props.get("SubState", "unknown"),
            "description": props.get("Description"),
            "enabled": props.get("UnitFileState") == "enabled",
            "main_pid": main_pid,
            "active_enter_timestamp": props.get("ActiveEnterTimestamp"),
        }
    }


def execute_service_action(action: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    service_name = validate_service_name(payload.get("service_name", ""))
    allowed_actions = {"start", "stop", "restart", "reload"}
    if action not in allowed_actions:
        raise ValueError(f"Aksi service '{action}' tidak diizinkan.")

    # Get previous state
    prev_status = execute_get_service_status({"service_name": service_name}).get("service")

    # Run systemctl action with sudo if needed
    cmd = ["systemctl", action, service_name]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    success = proc.returncode == 0

    # Get current state
    curr_status = execute_get_service_status({"service_name": service_name}).get("service")

    return {
        "success": success,
        "service": service_name,
        "action": action,
        "previous_state": prev_status,
        "current_state": curr_status,
        "message": f"Aksi {action} {service_name} {'berhasil' if success else 'gagal: ' + proc.stderr}",
    }


def execute_start_service(payload: Dict[str, Any]) -> Dict[str, Any]:
    return execute_service_action("start", payload)


def execute_stop_service(payload: Dict[str, Any]) -> Dict[str, Any]:
    return execute_service_action("stop", payload)


def execute_restart_service(payload: Dict[str, Any]) -> Dict[str, Any]:
    return execute_service_action("restart", payload)


def execute_reload_service(payload: Dict[str, Any]) -> Dict[str, Any]:
    return execute_service_action("reload", payload)
