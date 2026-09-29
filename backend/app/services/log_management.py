from datetime import datetime, timezone
import logging
import re
from typing import Optional
from fastapi import HTTPException, status

from app.infrastructure.log_providers.base import LogProvider
from app.infrastructure.log_providers.ssh_journal import (
    SINCE_MAP,
    SSHJournalLogProvider,
)
from app.models.server import Server
from app.schemas.log import LogEntry, LogResponse
from app.services.encryption import secret_encryption_service

logger = logging.getLogger(__name__)

SERVICE_NAME_PATTERN = re.compile(r"^[A-Za-z0-9_.@:-]+\.service$")


class LogManagementService:
    """Business logic for retrieving and managing service logs."""

    def __init__(self, log_provider: Optional[LogProvider] = None):
        self.log_provider = log_provider or SSHJournalLogProvider()

    def validate_service_name(self, service_name: str) -> str:
        cleaned = service_name.strip()
        if not SERVICE_NAME_PATTERN.match(cleaned):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    "Format nama service tidak valid. Nama service harus berakhiran '.service' "
                    "dan hanya memuat karakter alfanumerik, '.', '_', '-', '@', atau ':' tanpa spasi."
                ),
            )
        return cleaned

    def _extract_credentials(self, server: Server):
        if not server.credential:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Server belum memiliki kredensial SSH yang dikonfigurasi.",
            )

        cred = server.credential
        password = None
        private_key = None
        passphrase = None

        if cred.auth_type == "PASSWORD" and cred.encrypted_password:
            password = secret_encryption_service.decrypt(cred.encrypted_password)
        elif cred.auth_type == "PRIVATE_KEY" and cred.encrypted_private_key:
            private_key = secret_encryption_service.decrypt(cred.encrypted_private_key)
            if cred.encrypted_passphrase:
                passphrase = secret_encryption_service.decrypt(cred.encrypted_passphrase)

        return password, private_key, passphrase

    async def get_service_logs(
        self,
        server: Server,
        service_name: str,
        lines: int = 100,
        since: Optional[str] = None,
    ) -> LogResponse:
        valid_name = self.validate_service_name(service_name)

        if lines < 10 or lines > 1000:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Jumlah baris log (lines) harus bernilai antara 10 dan 1000.",
            )

        if since and since not in SINCE_MAP:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Nilai filter since '{since}' tidak valid. Pilihan yang didukung: {', '.join(SINCE_MAP.keys())}",
            )

        password, private_key, passphrase = self._extract_credentials(server)

        # Internal trace log (no secrets logged)
        logger.info(
            "Fetching logs for service=%s on server_id=%s (lines=%d, since=%s)",
            valid_name,
            server.id,
            lines,
            since,
        )

        res = await self.log_provider.get_service_logs(
            host=server.ip_address,
            port=server.ssh_port,
            username=server.username,
            password=password,
            private_key=private_key,
            passphrase=passphrase,
            service_name=valid_name,
            lines=lines,
            since=since,
        )

        if res.error == "INVALID_SERVICE_NAME":
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Nama service tidak valid.",
            )
        elif res.error == "SYSTEMD_UNAVAILABLE":
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Systemd logs tidak tersedia pada server ini.",
            )
        elif res.error == "TIMEOUT":
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="Permintaan log server batas waktu (timeout).",
            )
        elif res.error == "SSH_UNAVAILABLE":
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Tidak dapat terhubung ke server SSH.",
            )
        elif res.error == "INTERNAL_ERROR":
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Terjadi kesalahan saat mengambil log service.",
            )

        entries = [
            LogEntry(
                timestamp=e.timestamp,
                priority=e.priority,
                message=e.message,
            )
            for e in res.entries
        ]

        return LogResponse(
            server_id=server.id,
            service=valid_name,
            lines_requested=res.lines_requested,
            lines_returned=res.lines_returned,
            since=since,
            truncated=res.truncated,
            entries=entries,
            checked_at=datetime.now(timezone.utc),
        )


_log_management_service = LogManagementService()


def get_log_management_service() -> LogManagementService:
    return _log_management_service
