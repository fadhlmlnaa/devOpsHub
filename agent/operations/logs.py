import re
import subprocess
from typing import Dict, Any, List

SERVICE_NAME_PATTERN = re.compile(r"^[A-Za-z0-9_.@:-]+\.service$")


def validate_service_name(name: str) -> str:
    cleaned = name.strip()
    if not SERVICE_NAME_PATTERN.match(cleaned):
        raise ValueError(f"Nama service '{name}' tidak valid.")
    return cleaned


def execute_get_service_logs(payload: Dict[str, Any]) -> Dict[str, Any]:
    service_name = validate_service_name(payload.get("service_name", ""))
    lines = int(payload.get("lines", 100))
    since = payload.get("since")

    cmd = ["journalctl", "-u", service_name, "-n", str(lines), "--no-pager", "-o", "short-iso"]
    if since:
        since_map = {
            "15m": "15 min ago",
            "1h": "1 hour ago",
            "6h": "6 hours ago",
            "24h": "24 hours ago",
            "7d": "7 days ago",
        }
        if since in since_map:
            cmd.extend(["--since", since_map[since]])

    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
    entries = []
    for line in proc.stdout.splitlines():
        if line.strip():
            entries.append({"message": line, "priority": "INFO"})

    return {
        "entries": entries,
        "lines_requested": lines,
        "lines_returned": len(entries),
        "truncated": False,
    }
