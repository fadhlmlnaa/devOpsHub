import re
from typing import Optional
from app.schemas.monitoring import MemoryMetrics


def parse_meminfo(meminfo_content: str) -> MemoryMetrics:
    """Parses /proc/meminfo content into MemoryMetrics.
    
    Expected fields: MemTotal, MemFree, MemAvailable, Buffers, Cached.
    All values are converted from kB to bytes (* 1024).
    """
    try:
        mem_data = {}
        for line in meminfo_content.strip().splitlines():
            parts = line.split(":")
            if len(parts) == 2:
                key = parts[0].strip()
                val_parts = parts[1].strip().split()
                if val_parts and val_parts[0].isdigit():
                    mem_data[key] = int(val_parts[0])

        # If Darwin / macOS output fallback (sysctl hw.memsize & vm_stat)
        if "MemTotal" not in mem_data:
            darwin_total = re.search(r"hw\.memsize\s*[:=]\s*(\d+)", meminfo_content)
            if darwin_total:
                total_bytes = int(darwin_total.group(1))
                # rough estimation for darwin vm_stat if available
                free_pages_match = re.search(r"Pages free:\s*(\d+)", meminfo_content)
                page_size = 4096
                free_bytes = int(free_pages_match.group(1)) * page_size if free_pages_match else int(total_bytes * 0.3)
                available_bytes = free_bytes
                used_bytes = max(0, total_bytes - available_bytes)
                usage_pct = round((used_bytes / total_bytes) * 100.0, 2) if total_bytes > 0 else 0.0
                return MemoryMetrics(
                    total_bytes=total_bytes,
                    used_bytes=used_bytes,
                    available_bytes=available_bytes,
                    free_bytes=free_bytes,
                    usage_percent=usage_pct,
                )
            return MemoryMetrics(error="Format /proc/meminfo tidak valid atau data memori tidak ditemukan.")

        mem_total_kb = mem_data.get("MemTotal")
        if not mem_total_kb or mem_total_kb <= 0:
            return MemoryMetrics(error="MemTotal tidak ditemukan atau bernilai 0.")

        total_bytes = mem_total_kb * 1024
        free_bytes = (mem_data.get("MemFree") or 0) * 1024

        # MemAvailable is preferred in newer Linux kernels (>= 3.14)
        if "MemAvailable" in mem_data and mem_data["MemAvailable"] is not None:
            available_bytes = mem_data["MemAvailable"] * 1024
        else:
            buffers = (mem_data.get("Buffers") or 0) * 1024
            cached = (mem_data.get("Cached") or 0) * 1024
            available_bytes = free_bytes + buffers + cached

        available_bytes = min(total_bytes, max(0, available_bytes))
        used_bytes = max(0, total_bytes - available_bytes)

        usage_pct = round((used_bytes / total_bytes) * 100.0, 2)
        usage_pct = max(0.0, min(100.0, usage_pct))

        return MemoryMetrics(
            total_bytes=total_bytes,
            used_bytes=used_bytes,
            available_bytes=available_bytes,
            free_bytes=free_bytes,
            usage_percent=usage_pct,
        )

    except Exception as e:
        return MemoryMetrics(error=f"Gagal memproses metrik memori: {str(e)}")
