import re
import uuid
from datetime import datetime, timezone
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.infrastructure.service_providers.base import ServiceProvider
from app.infrastructure.service_providers.ssh_systemd import SSHSystemdProvider
from app.models.server import Server
from app.models.workspace_member import WorkspaceRole
from app.schemas.service import (
    ServiceActionResponse,
    ServiceDetailResponse,
    ServiceListResponse,
    ServiceStateSummary,
    ServiceSummary,
)
from app.services.encryption import secret_encryption_service

SERVICE_NAME_PATTERN = re.compile(r"^[A-Za-z0-9_.@:-]+\.service$")


class ServiceManagementService:
    """Business logic for Linux systemd service management."""

    def __init__(self, service_provider: Optional[ServiceProvider] = None):
        self.service_provider = service_provider or SSHSystemdProvider()

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

    async def list_services(
        self,
        server: Server,
        state: Optional[str] = None,
        limit: int = 100,
    ) -> ServiceListResponse:
        password, private_key, passphrase = self._extract_credentials(server)

        result = await self.service_provider.list_services(
            host=server.ip_address,
            port=server.ssh_port,
            username=server.username,
            password=password,
            private_key=private_key,
            passphrase=passphrase,
            state=state,
            limit=limit,
        )

        checked_at = datetime.now(timezone.utc)
        summaries = [
            ServiceSummary(
                name=s.name,
                load_state=s.load_state,
                active_state=s.active_state,
                sub_state=s.sub_state,
                description=s.description,
                enabled=s.enabled,
            )
            for s in result.services
        ]

        return ServiceListResponse(
            server_id=server.id,
            systemd_supported=result.systemd_supported,
            services=summaries,
            checked_at=checked_at,
            message=result.error_message,
        )

    async def get_service(
        self,
        server: Server,
        service_name: str,
    ) -> ServiceDetailResponse:
        valid_name = self.validate_service_name(service_name)
        password, private_key, passphrase = self._extract_credentials(server)

        info = await self.service_provider.get_service(
            host=server.ip_address,
            port=server.ssh_port,
            username=server.username,
            password=password,
            private_key=private_key,
            passphrase=passphrase,
            service_name=valid_name,
        )

        if not info or info.load_state == "not-found":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Service '{valid_name}' tidak ditemukan pada server.",
            )

        return ServiceDetailResponse(
            server_id=server.id,
            name=info.name,
            load_state=info.load_state,
            active_state=info.active_state,
            sub_state=info.sub_state,
            enabled=info.enabled,
            description=info.description,
            main_pid=info.main_pid,
            active_enter_timestamp=info.active_enter_timestamp,
            checked_at=datetime.now(timezone.utc),
        )

    async def execute_action(
        self,
        server: Server,
        service_name: str,
        action: str,
        confirm: bool,
    ) -> ServiceActionResponse:
        valid_name = self.validate_service_name(service_name)
        if not confirm:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Konfirmasi eksplisit diperlukan untuk menjalankan aksi service (confirm=true).",
            )

        password, private_key, passphrase = self._extract_credentials(server)

        res = await self.service_provider.execute_action(
            host=server.ip_address,
            port=server.ssh_port,
            username=server.username,
            password=password,
            private_key=private_key,
            passphrase=passphrase,
            service_name=valid_name,
            action=action,
        )

        if res.error == "TIMEOUT":
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail=res.message,
            )
        elif res.error == "SUDO_PASSWORD_REQUIRED":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=res.message,
            )
        elif res.error == "INVALID_SERVICE_NAME":
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=res.message,
            )
        elif res.error == "INVALID_ACTION":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=res.message,
            )

        prev_state = (
            ServiceStateSummary(
                active_state=res.previous_state.get("active_state", "unknown"),
                sub_state=res.previous_state.get("sub_state", "unknown"),
            )
            if res.previous_state
            else None
        )

        curr_state = (
            ServiceStateSummary(
                active_state=res.current_state.get("active_state", "unknown"),
                sub_state=res.current_state.get("sub_state", "unknown"),
            )
            if res.current_state
            else None
        )

        return ServiceActionResponse(
            success=res.success,
            service=res.service,
            action=res.action,
            previous_state=prev_state,
            current_state=curr_state,
            message=res.message,
            checked_at=datetime.now(timezone.utc),
        )


_service_management_service = ServiceManagementService()


def get_service_management_service() -> ServiceManagementService:
    return _service_management_service
