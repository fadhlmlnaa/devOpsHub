import re
from typing import Optional, Tuple
from app.schemas.monitoring import SystemInfoMetrics


def parse_uptime_seconds(uptime_content: str) -> Optional[int]:
    """Parses /proc/uptime (or sysctl kern.boottime or uptime string) to total uptime in seconds.
    
    Format of /proc/uptime:
    1555200.45 3110400.90
    """
    try:
        cleaned = uptime_content.strip()
        if not cleaned:
            return None

        # Check standard /proc/uptime
        parts = cleaned.split()
        if parts and re.match(r"^\d+(\.\d+)?$", parts[0]):
            return int(float(parts[0]))

        # Check for Darwin uptime string, e.g. "up 18 days, 4:20" or "up 2 hours"
        days_match = re.search(r"up\s+(\d+)\s+day", cleaned)
        hours_match = re.search(r"(\d+):(\d+)", cleaned)
        min_match = re.search(r"(\d+)\s+min", cleaned)

        total_sec = 0
        if days_match:
            total_sec += int(days_match.group(1)) * 86400
        if hours_match:
            total_sec += int(hours_match.group(1)) * 3600 + int(hours_match.group(2)) * 60
        elif min_match:
            total_sec += int(min_match.group(1)) * 60

        return total_sec if total_sec > 0 else None

    except Exception:
        return None


def parse_system_info(
    hostname_raw: Optional[str] = None,
    os_release_raw: Optional[str] = None,
    kernel_raw: Optional[str] = None,
    arch_raw: Optional[str] = None,
) -> SystemInfoMetrics:
    """Parses system identifiers into SystemInfoMetrics."""
    hostname = hostname_raw.strip() if hostname_raw else None
    kernel = kernel_raw.strip() if kernel_raw else None
    arch = arch_raw.strip() if arch_raw else None

    os_name = None
    if os_release_raw:
        # Check PRETTY_NAME="Ubuntu 24.04.1 LTS"
        match = re.search(r'PRETTY_NAME=["\']?([^"\']+)["\']?', os_release_raw)
        if match:
            os_name = match.group(1).strip()
        else:
            first_line = os_release_raw.strip().splitlines()[0]
            if first_line:
                os_name = first_line.strip()

    return SystemInfoMetrics(
        hostname=hostname,
        operating_system=os_name,
        kernel=kernel,
        architecture=arch,
    )
