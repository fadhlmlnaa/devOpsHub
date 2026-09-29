import subprocess
import os
import shutil
from typing import Dict, Any


def execute_get_system_metrics(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Predefined safe collector for system telemetry metrics."""
    batch_script = (
        'echo "===CPU==="; head -n 20 /proc/stat 2>/dev/null || top -l 1 -n 0 2>/dev/null\n'
        'echo "===CPUINFO==="; nproc 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || grep -c ^processor /proc/cpuinfo 2>/dev/null\n'
        'echo "===MEM==="; head -n 30 /proc/meminfo 2>/dev/null || (sysctl hw.memsize 2>/dev/null; vm_stat 2>/dev/null)\n'
        'echo "===DISK==="; df -k / 2>/dev/null\n'
        'echo "===LOAD==="; cat /proc/loadavg 2>/dev/null || sysctl -n vm.loadavg 2>/dev/null || uptime 2>/dev/null\n'
        'echo "===UPTIME==="; cat /proc/uptime 2>/dev/null || uptime 2>/dev/null\n'
        'echo "===SYSTEM==="; hostname 2>/dev/null; echo "---"; cat /etc/os-release 2>/dev/null || uname -s 2>/dev/null; echo "---"; uname -r 2>/dev/null; echo "---"; uname -m 2>/dev/null\n'
        'echo "===NET==="; ip -j addr 2>/dev/null || ip addr 2>/dev/null || ifconfig 2>/dev/null\n'
    )

    proc = subprocess.run(
        ["/bin/sh", "-c", batch_script],
        capture_output=True,
        text=True,
        timeout=10,
    )

    raw_output = proc.stdout or ""
    sections: Dict[str, str] = {}
    current_section = None
    current_lines = []

    for line in raw_output.splitlines():
        if line.startswith("===") and line.endswith("==="):
            if current_section:
                sections[current_section] = "\n".join(current_lines).strip()
            current_section = line.replace("===", "").strip()
            current_lines = []
        else:
            current_lines.append(line)

    if current_section:
        sections[current_section] = "\n".join(current_lines).strip()

    return {"sections": sections}


def execute_get_server_info(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Lightweight server info collector."""
    import platform
    return {
        "hostname": platform.node(),
        "operating_system": f"{platform.system()} {platform.release()}",
        "architecture": platform.machine(),
        "python_version": platform.python_version(),
    }
