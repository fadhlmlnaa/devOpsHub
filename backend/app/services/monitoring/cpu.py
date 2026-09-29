import re
from typing import Optional, Tuple
from app.schemas.monitoring import CPUMetrics


def parse_cpu_stat(proc_stat_content: str, cpuinfo_content: Optional[str] = None) -> CPUMetrics:
    """Parses /proc/stat content (and optional /proc/cpuinfo or nproc) into CPUMetrics.
    
    Format of first line of /proc/stat:
    cpu  user nice system idle iowait irq softirq steal guest guest_nice
    """
    try:
        lines = proc_stat_content.strip().splitlines()
        cpu_line = None
        core_count = 0

        for line in lines:
            line_str = line.strip()
            if line_str.startswith("cpu "):
                cpu_line = line_str
            elif re.match(r"^cpu\d+", line_str):
                core_count += 1

        if not cpu_line:
            # Check for Darwin / fallback format (e.g. "CPU usage: 12.3% user, 4.5% sys, 83.2% idle")
            darwin_match = re.search(r"CPU usage:\s*([\d\.]+)%\s*user,\s*([\d\.]+)%\s*sys,\s*([\d\.]+)%\s*idle", proc_stat_content)
            if darwin_match:
                user = float(darwin_match.group(1))
                sys = float(darwin_match.group(2))
                usage = round(user + sys, 2)
                usage = max(0.0, min(100.0, usage))
                cores = int(cpuinfo_content.strip()) if cpuinfo_content and cpuinfo_content.strip().isdigit() else max(1, core_count)
                return CPUMetrics(usage_percent=usage, cores=cores)
            return CPUMetrics(error="Format /proc/stat tidak valid atau data CPU tidak ditemukan.")

        parts = cpu_line.split()
        if len(parts) < 5:
            return CPUMetrics(error="Baris CPU pada /proc/stat tidak lengkap.")

        # values: user, nice, system, idle, iowait, irq, softirq, steal
        values = [float(x) for x in parts[1:]]
        user = values[0]
        nice = values[1] if len(values) > 1 else 0.0
        system = values[2] if len(values) > 2 else 0.0
        idle = values[3] if len(values) > 3 else 0.0
        iowait = values[4] if len(values) > 4 else 0.0
        irq = values[5] if len(values) > 5 else 0.0
        softirq = values[6] if len(values) > 6 else 0.0
        steal = values[7] if len(values) > 7 else 0.0

        total_ticks = sum(values)
        idle_ticks = idle + iowait
        used_ticks = total_ticks - idle_ticks

        if total_ticks <= 0:
            usage_pct = 0.0
        else:
            usage_pct = round((used_ticks / total_ticks) * 100.0, 2)

        usage_pct = max(0.0, min(100.0, usage_pct))

        # Core count from cpuinfo if available
        if cpuinfo_content:
            cpuinfo_str = cpuinfo_content.strip()
            if cpuinfo_str.isdigit():
                core_count = max(1, int(cpuinfo_str))
            else:
                proc_matches = re.findall(r"^processor\s*:\s*\d+", cpuinfo_content, re.MULTILINE)
                if proc_matches:
                    core_count = max(1, len(proc_matches))

        if core_count <= 0:
            core_count = 1

        return CPUMetrics(
            usage_percent=usage_pct,
            cores=core_count,
        )

    except Exception as e:
        return CPUMetrics(error=f"Gagal memproses metrik CPU: {str(e)}")
