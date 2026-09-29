import logging
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session

from app.models.server import Server
from app.schemas.monitoring import ServerMetricsResponse
from app.services.encryption import secret_encryption_service
from app.services.connection_provider import ConnectionProvider, get_connection_provider
from app.services.monitoring.cpu import parse_cpu_stat
from app.services.monitoring.memory import parse_meminfo
from app.services.monitoring.disk import parse_df_output
from app.services.monitoring.load import parse_loadavg
from app.services.monitoring.system_info import parse_system_info, parse_uptime_seconds
from app.services.monitoring.network import parse_network_interfaces

logger = logging.getLogger(__name__)


class MonitoringService:
    """Service to collect and assemble telemetry metrics from remote servers."""

    def __init__(self, provider: Optional[ConnectionProvider] = None):
        self._custom_provider = provider

    def _get_provider(self, server: Server, db: Optional[Session] = None) -> ConnectionProvider:
        if self._custom_provider:
            return self._custom_provider
        return get_connection_provider(server, db)

    async def get_server_metrics(self, server: Server, db: Optional[Session] = None) -> ServerMetricsResponse:
        """Fetches telemetry metrics from the server using the configured connection provider."""
        # 1. Determine connection target
        host = server.ip_address or server.hostname or ""
        if not host and server.connection_type != "AGENT":
            return ServerMetricsResponse(
                server_id=server.id,
                status="UNKNOWN",
                checked_at=datetime.utcnow(),
                error="Server tidak memiliki IP Address atau Hostname yang valid.",
            )

        port = server.ssh_port or 22
        username = server.username or "root"
        password = None
        private_key = None
        passphrase = None

        # 2. Extract decrypted credentials if available
        if server.connection_type != "AGENT" and server.credential:
            cred = server.credential
            username = cred.username or username
            if cred.encrypted_password:
                try:
                    password = secret_encryption_service.decrypt(cred.encrypted_password)
                except Exception as e:
                    logger.error("Failed to decrypt server password: %s", type(e).__name__)
                    return ServerMetricsResponse(
                        server_id=server.id,
                        status="UNKNOWN",
                        checked_at=datetime.utcnow(),
                        error="Gagal mendekripsi password server.",
                    )

            if cred.encrypted_private_key:
                try:
                    private_key = secret_encryption_service.decrypt(cred.encrypted_private_key)
                except Exception as e:
                    logger.error("Failed to decrypt server private key: %s", type(e).__name__)
                    return ServerMetricsResponse(
                        server_id=server.id,
                        status="UNKNOWN",
                        checked_at=datetime.utcnow(),
                        error="Gagal mendekripsi SSH private key server.",
                    )

            if cred.encrypted_passphrase:
                try:
                    passphrase = secret_encryption_service.decrypt(cred.encrypted_passphrase)
                except Exception:
                    pass

        # 3. Collect raw telemetry via ConnectionProvider
        provider = self._get_provider(server, db)
        raw_res = await provider.collect_raw_metrics(
            host=host,
            port=port,
            username=username,
            password=password,
            private_key=private_key,
            passphrase=passphrase,
        )

        checked_at = datetime.utcnow()

        if not raw_res.get("success", False):
            return ServerMetricsResponse(
                server_id=server.id,
                status=raw_res.get("status", "OFFLINE"),
                checked_at=checked_at,
                error=raw_res.get("error", "Gagal mengumpulkan data monitoring dari server."),
            )

        sections = raw_res.get("sections", {})

        # 4. Parse individual metrics
        cpu_metrics = parse_cpu_stat(sections.get("CPU", ""), sections.get("CPUINFO", ""))
        memory_metrics = parse_meminfo(sections.get("MEM", ""))
        disk_metrics = parse_df_output(sections.get("DISK", ""), mount_point="/")
        load_metrics = parse_loadavg(sections.get("LOAD", ""))
        uptime_sec = parse_uptime_seconds(sections.get("UPTIME", ""))

        # Parse system info from delimiter '---'
        sys_raw = sections.get("SYSTEM", "")
        sys_parts = [p.strip() for p in sys_raw.split("---")]
        hostname_val = sys_parts[0] if len(sys_parts) > 0 else server.hostname
        os_val = sys_parts[1] if len(sys_parts) > 1 else server.operating_system
        kernel_val = sys_parts[2] if len(sys_parts) > 2 else None
        arch_val = sys_parts[3] if len(sys_parts) > 3 else None

        system_metrics = parse_system_info(
            hostname_raw=hostname_val,
            os_release_raw=os_val,
            kernel_raw=kernel_val,
            arch_raw=arch_val,
        )

        network_metrics = parse_network_interfaces(sections.get("NET", ""))

        return ServerMetricsResponse(
            server_id=server.id,
            status="ONLINE",
            checked_at=checked_at,
            cpu=cpu_metrics,
            memory=memory_metrics,
            disk=disk_metrics,
            load=load_metrics,
            uptime_seconds=uptime_sec,
            system=system_metrics,
            network=network_metrics,
        )
