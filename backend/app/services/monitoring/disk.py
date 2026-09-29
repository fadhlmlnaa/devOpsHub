import re
from typing import Optional
from app.schemas.monitoring import DiskMetrics


def parse_df_output(df_content: str, mount_point: str = "/") -> DiskMetrics:
    """Parses 'df -k /' output into DiskMetrics.
    
    Expected format:
    Filesystem     1K-blocks    Used Available Use% Mounted on
    /dev/sda1      104857600 73400320  31457280  70% /
    """
    try:
        lines = [line.strip() for line in df_content.strip().splitlines() if line.strip()]
        if len(lines) < 2:
            return DiskMetrics(mount_point=mount_point, error="Output command df kosong atau tidak valid.")

        # Header is usually first line, target mount point is on second (or last) line
        data_line = lines[-1]
        parts = data_line.split()

        # Some filesystems wrap line if filesystem name is very long
        if len(parts) < 5 and len(lines) >= 3:
            # Combine second-to-last and last
            parts = (lines[-2] + " " + lines[-1]).split()

        if len(parts) < 5:
            return DiskMetrics(mount_point=mount_point, error=f"Format baris df tidak lengkap: '{data_line}'")

        filesystem = parts[0]
        # In df -k:
        # parts: [Filesystem, 1K-blocks, Used, Available, Use%, Mounted_on]
        total_1k = int(parts[1]) if parts[1].isdigit() else 0
        used_1k = int(parts[2]) if parts[2].isdigit() else 0
        avail_1k = int(parts[3]) if parts[3].isdigit() else 0

        if total_1k <= 0:
            return DiskMetrics(
                filesystem=filesystem,
                mount_point=mount_point,
                error="Kapasitas total disk terbaca 0 atau tidak valid.",
            )

        total_bytes = total_1k * 1024
        used_bytes = used_1k * 1024
        available_bytes = avail_1k * 1024

        usage_pct = round((used_bytes / total_bytes) * 100.0, 2)
        usage_pct = max(0.0, min(100.0, usage_pct))

        return DiskMetrics(
            filesystem=filesystem,
            mount_point=mount_point,
            total_bytes=total_bytes,
            used_bytes=used_bytes,
            available_bytes=available_bytes,
            usage_percent=usage_pct,
        )

    except Exception as e:
        return DiskMetrics(mount_point=mount_point, error=f"Gagal memproses metrik disk: {str(e)}")
