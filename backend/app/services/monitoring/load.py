import re
from typing import Optional
from app.schemas.monitoring import LoadMetrics


def parse_loadavg(loadavg_content: str) -> LoadMetrics:
    """Parses /proc/loadavg content (or sysctl vm.loadavg / uptime output) into LoadMetrics.
    
    Expected format in Linux /proc/loadavg:
    0.82 0.64 0.51 1/450 12345
    """
    try:
        cleaned = loadavg_content.strip()
        if not cleaned:
            return LoadMetrics(error="Data load average kosong.")

        # Check for Darwin sysctl: "{ 0.82 0.64 0.51 }"
        cleaned = cleaned.replace("{", "").replace("}", "").replace(",", "").strip()

        # Check if uptime format: "load average: 0.82, 0.64, 0.51"
        if "load average" in cleaned.lower():
            match = re.search(r"load averages?:\s*([\d\.]+)\s+([\d\.]+)\s+([\d\.]+)", cleaned, re.IGNORECASE)
            if match:
                return LoadMetrics(
                    load_1m=float(match.group(1)),
                    load_5m=float(match.group(2)),
                    load_15m=float(match.group(3)),
                )

        parts = cleaned.split()
        if len(parts) < 3:
            return LoadMetrics(error=f"Format /proc/loadavg tidak valid: '{loadavg_content.strip()}'")

        load_1m = float(parts[0])
        load_5m = float(parts[1])
        load_15m = float(parts[2])

        return LoadMetrics(
            load_1m=load_1m,
            load_5m=load_5m,
            load_15m=load_15m,
        )

    except Exception as e:
        return LoadMetrics(error=f"Gagal memproses load average: {str(e)}")
