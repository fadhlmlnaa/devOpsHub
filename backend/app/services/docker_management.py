import re
import uuid
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.infrastructure.docker_providers.base import DockerProvider
from app.infrastructure.docker_providers.ssh_docker import SSHDockerProvider
from app.models.docker_compose import DockerComposeProject
from app.models.environment import Environment
from app.models.server import Server
from app.models.workspace_member import WorkspaceRole
from app.schemas.docker import (
    CONTAINER_ID_PATTERN,
    ComposeProjectStatus,
    ContainerFilterState,
    DockerComposeActionResult,
    DockerComposeProjectCreate,
    DockerComposeProjectResponse,
    DockerComposeProjectUpdate,
    DockerComposeServiceStatus,
    DockerComposeStatusResponse,
    DockerContainerActionResult,
    DockerContainerDetail,
    DockerContainerListResponse,
    DockerContainerLogsResponse,
    DockerContainerSummary,
    DockerDaemonState,
    DockerLogEntry,
    DockerStatusResponse,
)
from app.services.encryption import secret_encryption_service
from app.services.provider_factory import ProviderFactory


class DockerManagementService:
    """Business logic for Docker & Docker Compose container management."""

    def __init__(self, docker_provider: Optional[DockerProvider] = None):
        self._custom_provider = docker_provider

    def _get_provider(self, server: Server, db: Session) -> DockerProvider:
        if self._custom_provider:
            return self._custom_provider
        return ProviderFactory.get_docker_provider(server, db)

    def validate_container_id(self, container_id: str) -> str:
        clean_id = container_id.strip()
        if not CONTAINER_ID_PATTERN.match(clean_id):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    "Format container ID atau nama container tidak valid. "
                    "Hanya karakter alfanumerik, '.', '_', dan '-' yang diizinkan."
                ),
            )
        return clean_id

    def _extract_credentials(self, server: Server):
        if server.connection_type == "AGENT":
            return (
                server.ip_address or server.hostname or "",
                server.ssh_port or 22,
                server.username or "root",
                None,
                None,
                None,
            )

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

        return (
            server.ip_address or server.hostname,
            server.ssh_port,
            server.username or "root",
            password,
            private_key,
            passphrase,
        )

    # --- 1. Docker Daemon Status ---
    async def get_docker_status(
        self,
        db: Session,
        workspace_id: uuid.UUID,
        server_id: uuid.UUID,
        user_id: uuid.UUID,
        user_role: WorkspaceRole,
    ) -> DockerStatusResponse:
        server = db.query(Server).filter(
            Server.id == server_id,
            Server.workspace_id == workspace_id,
        ).first()
        if not server:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Server tidak ditemukan.")

        host, port, username, password, private_key, passphrase = self._extract_credentials(server)
        provider = self._get_provider(server, db)
        res = await provider.get_docker_status(
            host, port, username, password, private_key, passphrase
        )

        state_enum = DockerDaemonState.UNKNOWN
        if res.state == "RUNNING":
            state_enum = DockerDaemonState.RUNNING
        elif res.state == "STOPPED":
            state_enum = DockerDaemonState.STOPPED
        elif res.state == "NOT_INSTALLED":
            state_enum = DockerDaemonState.NOT_INSTALLED

        return DockerStatusResponse(
            server_id=server_id,
            installed=res.installed,
            running=res.running,
            version=res.version,
            state=state_enum,
            checked_at=datetime.now(timezone.utc),
        )

    # --- 2. Container List ---
    async def list_containers(
        self,
        db: Session,
        workspace_id: uuid.UUID,
        server_id: uuid.UUID,
        user_id: uuid.UUID,
        user_role: WorkspaceRole,
        state_filter: ContainerFilterState = ContainerFilterState.RUNNING,
    ) -> DockerContainerListResponse:
        server = db.query(Server).filter(
            Server.id == server_id,
            Server.workspace_id == workspace_id,
        ).first()
        if not server:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Server tidak ditemukan.")

        host, port, username, password, private_key, passphrase = self._extract_credentials(server)
        provider = self._get_provider(server, db)
        results = await provider.list_containers(
            host, port, username, password, private_key, passphrase,
            state_filter=state_filter.value,
        )

        containers = [
            DockerContainerSummary(
                id=c.id,
                name=c.name,
                image=c.image,
                status=c.status,
                state=c.state,
                created_at=c.created_at,
                ports=c.ports,
            )
            for c in results
        ]

        return DockerContainerListResponse(
            server_id=server_id,
            containers=containers,
            checked_at=datetime.now(timezone.utc),
        )

    # --- 3. Container Detail ---
    async def get_container_detail(
        self,
        db: Session,
        workspace_id: uuid.UUID,
        server_id: uuid.UUID,
        container_id: str,
        user_id: uuid.UUID,
        user_role: WorkspaceRole,
    ) -> DockerContainerDetail:
        valid_id = self.validate_container_id(container_id)
        server = db.query(Server).filter(
            Server.id == server_id,
            Server.workspace_id == workspace_id,
        ).first()
        if not server:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Server tidak ditemukan.")

        host, port, username, password, private_key, passphrase = self._extract_credentials(server)
        provider = self._get_provider(server, db)
        c = await provider.get_container_detail(
            host, port, username, password, private_key, passphrase,
            container_id=valid_id,
        )

        if not c:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Container '{valid_id}' tidak ditemukan pada server ini.",
            )

        return DockerContainerDetail(
            id=c.id,
            name=c.name,
            image=c.image,
            state=c.state,
            status=c.status,
            created_at=c.created_at,
            started_at=c.started_at,
            ports=c.ports,
            restart_policy=c.restart_policy,
            cpu_usage=c.cpu_usage,
            memory_usage=c.memory_usage,
            checked_at=datetime.now(timezone.utc),
        )

    # --- 4. Container Actions (Start/Stop/Restart) ---
    async def execute_container_action(
        self,
        db: Session,
        workspace_id: uuid.UUID,
        server_id: uuid.UUID,
        container_id: str,
        action: str,
        confirm: bool,
        user_id: uuid.UUID,
        user_role: WorkspaceRole,
    ) -> DockerContainerActionResult:
        # Authorization check: only OWNER & ADMIN can perform container actions
        if user_role not in [WorkspaceRole.OWNER, WorkspaceRole.ADMIN]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Anda tidak memiliki izin untuk memodifikasi container pada workspace ini.",
            )

        if not confirm:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Konfirmasi eksplisit diperlukan untuk menjalankan aksi '{action}' pada container.",
            )

        valid_id = self.validate_container_id(container_id)
        server = db.query(Server).filter(
            Server.id == server_id,
            Server.workspace_id == workspace_id,
        ).first()
        if not server:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Server tidak ditemukan.")

        host, port, username, password, private_key, passphrase = self._extract_credentials(server)
        provider = self._get_provider(server, db)
        res = await provider.execute_container_action(
            host, port, username, password, private_key, passphrase,
            container_id=valid_id,
            action=action,
        )

        return DockerContainerActionResult(
            success=res.success,
            container=res.container,
            action=res.action,
            current_state=res.current_state,
            message=res.message,
            checked_at=datetime.now(timezone.utc),
        )

    # --- 5. Container Logs ---
    async def get_container_logs(
        self,
        db: Session,
        workspace_id: uuid.UUID,
        server_id: uuid.UUID,
        container_id: str,
        user_id: uuid.UUID,
        user_role: WorkspaceRole,
        lines: int = 100,
        since: Optional[str] = None,
    ) -> DockerContainerLogsResponse:
        valid_id = self.validate_container_id(container_id)
        server = db.query(Server).filter(
            Server.id == server_id,
            Server.workspace_id == workspace_id,
        ).first()
        if not server:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Server tidak ditemukan.")

        host, port, username, password, private_key, passphrase = self._extract_credentials(server)
        provider = self._get_provider(server, db)
        res = await provider.get_container_logs(
            host, port, username, password, private_key, passphrase,
            container_id=valid_id,
            lines=lines,
            since=since,
        )

        if res.error == "SSH_UNAVAILABLE":
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Unable to connect to server.",
            )
        elif res.error == "TIMEOUT":
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="Log request timed out.",
            )

        entries = [
            DockerLogEntry(timestamp=e.timestamp, message=e.message)
            for e in res.entries
        ]

        return DockerContainerLogsResponse(
            container=res.container,
            lines_requested=res.lines_requested,
            lines_returned=res.lines_returned,
            entries=entries,
            truncated=res.truncated,
            checked_at=datetime.now(timezone.utc),
        )

    # --- 6. Docker Compose Project CRUD ---
    def list_compose_projects(
        self,
        db: Session,
        workspace_id: uuid.UUID,
        server_id: uuid.UUID,
        user_id: uuid.UUID,
        user_role: WorkspaceRole,
    ) -> List[DockerComposeProjectResponse]:
        server = db.query(Server).filter(
            Server.id == server_id,
            Server.workspace_id == workspace_id,
        ).first()
        if not server:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Server tidak ditemukan.")

        projects = db.query(DockerComposeProject).filter(
            DockerComposeProject.workspace_id == workspace_id,
            DockerComposeProject.server_id == server_id,
        ).order_by(DockerComposeProject.created_at.desc()).all()

        return [DockerComposeProjectResponse.model_validate(p) for p in projects]

    def create_compose_project(
        self,
        db: Session,
        workspace_id: uuid.UUID,
        server_id: uuid.UUID,
        user_id: uuid.UUID,
        user_role: WorkspaceRole,
        data_in: DockerComposeProjectCreate,
    ) -> DockerComposeProjectResponse:
        if user_role not in [WorkspaceRole.OWNER, WorkspaceRole.ADMIN]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Hanya Administrator dan Owner yang dapat mendaftarkan Docker Compose project.",
            )

        server = db.query(Server).filter(
            Server.id == server_id,
            Server.workspace_id == workspace_id,
        ).first()
        if not server:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Server tidak ditemukan.")

        # Verify environment exists in workspace
        env = db.query(Environment).filter(
            Environment.id == data_in.environment_id,
            Environment.workspace_id == workspace_id,
        ).first()
        if not env:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Environment tidak ditemukan pada workspace ini.",
            )

        # Check duplicate project_name on same server
        existing = db.query(DockerComposeProject).filter(
            DockerComposeProject.server_id == server_id,
            DockerComposeProject.project_name == data_in.project_name,
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Project dengan nama '{data_in.project_name}' sudah terdaftar pada server ini.",
            )

        project = DockerComposeProject(
            workspace_id=workspace_id,
            server_id=server_id,
            environment_id=data_in.environment_id,
            name=data_in.name,
            project_name=data_in.project_name,
            working_directory=data_in.working_directory,
            compose_file=data_in.compose_file,
            description=data_in.description,
            is_active=data_in.is_active,
        )
        db.add(project)
        db.commit()
        db.refresh(project)

        return DockerComposeProjectResponse.model_validate(project)

    def get_compose_project(
        self,
        db: Session,
        workspace_id: uuid.UUID,
        server_id: uuid.UUID,
        project_id: uuid.UUID,
        user_id: uuid.UUID,
        user_role: WorkspaceRole,
    ) -> DockerComposeProjectResponse:
        project = db.query(DockerComposeProject).filter(
            DockerComposeProject.id == project_id,
            DockerComposeProject.server_id == server_id,
            DockerComposeProject.workspace_id == workspace_id,
        ).first()
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Docker Compose project tidak ditemukan.")

        return DockerComposeProjectResponse.model_validate(project)

    def update_compose_project(
        self,
        db: Session,
        workspace_id: uuid.UUID,
        server_id: uuid.UUID,
        project_id: uuid.UUID,
        user_id: uuid.UUID,
        user_role: WorkspaceRole,
        data_in: DockerComposeProjectUpdate,
    ) -> DockerComposeProjectResponse:
        if user_role not in [WorkspaceRole.OWNER, WorkspaceRole.ADMIN]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Hanya Administrator dan Owner yang dapat mengubah Docker Compose project.",
            )

        project = db.query(DockerComposeProject).filter(
            DockerComposeProject.id == project_id,
            DockerComposeProject.server_id == server_id,
            DockerComposeProject.workspace_id == workspace_id,
        ).first()
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Docker Compose project tidak ditemukan.")

        if data_in.environment_id is not None:
            env = db.query(Environment).filter(
                Environment.id == data_in.environment_id,
                Environment.workspace_id == workspace_id,
            ).first()
            if not env:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Environment tidak valid.")
            project.environment_id = data_in.environment_id

        if data_in.name is not None:
            project.name = data_in.name
        if data_in.project_name is not None:
            project.project_name = data_in.project_name
        if data_in.working_directory is not None:
            project.working_directory = data_in.working_directory
        if data_in.compose_file is not None:
            project.compose_file = data_in.compose_file
        if data_in.description is not None:
            project.description = data_in.description
        if data_in.is_active is not None:
            project.is_active = data_in.is_active

        db.commit()
        db.refresh(project)
        return DockerComposeProjectResponse.model_validate(project)

    def delete_compose_project(
        self,
        db: Session,
        workspace_id: uuid.UUID,
        server_id: uuid.UUID,
        project_id: uuid.UUID,
        user_id: uuid.UUID,
        user_role: WorkspaceRole,
    ):
        if user_role not in [WorkspaceRole.OWNER, WorkspaceRole.ADMIN]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Hanya Administrator dan Owner yang dapat menghapus Docker Compose project.",
            )

        project = db.query(DockerComposeProject).filter(
            DockerComposeProject.id == project_id,
            DockerComposeProject.server_id == server_id,
            DockerComposeProject.workspace_id == workspace_id,
        ).first()
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Docker Compose project tidak ditemukan.")

        db.delete(project)
        db.commit()

    # --- 7. Docker Compose Operations (Status / Up / Down / Restart) ---
    async def get_compose_status(
        self,
        db: Session,
        workspace_id: uuid.UUID,
        server_id: uuid.UUID,
        project_id: uuid.UUID,
        user_id: uuid.UUID,
        user_role: WorkspaceRole,
    ) -> DockerComposeStatusResponse:
        project = db.query(DockerComposeProject).filter(
            DockerComposeProject.id == project_id,
            DockerComposeProject.server_id == server_id,
            DockerComposeProject.workspace_id == workspace_id,
        ).first()
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Docker Compose project tidak ditemukan.")

        server = project.server
        host, port, username, password, private_key, passphrase = self._extract_credentials(server)
        provider = self._get_provider(server, db)
        res = await provider.get_compose_status(
            host, port, username, password, private_key, passphrase,
            working_directory=project.working_directory,
            compose_file=project.compose_file,
            project_name=project.project_name,
        )

        services = [
            DockerComposeServiceStatus(
                name=s.name,
                service=s.service,
                state=s.state,
                status=s.status,
            )
            for s in res.services
        ]

        status_enum = ComposeProjectStatus.UNKNOWN
        try:
            status_enum = ComposeProjectStatus[res.status]
        except Exception:
            pass

        return DockerComposeStatusResponse(
            project_id=project.id,
            project_name=project.project_name,
            status=status_enum,
            services=services,
            checked_at=datetime.now(timezone.utc),
        )

    async def execute_compose_action(
        self,
        db: Session,
        workspace_id: uuid.UUID,
        server_id: uuid.UUID,
        project_id: uuid.UUID,
        action: str,
        confirm: bool,
        user_id: uuid.UUID,
        user_role: WorkspaceRole,
    ) -> DockerComposeActionResult:
        if user_role not in [WorkspaceRole.OWNER, WorkspaceRole.ADMIN]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Hanya Administrator dan Owner yang dapat menjalankan operasi Docker Compose.",
            )

        if not confirm:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Konfirmasi eksplisit diperlukan untuk menjalankan compose '{action}'.",
            )

        project = db.query(DockerComposeProject).filter(
            DockerComposeProject.id == project_id,
            DockerComposeProject.server_id == server_id,
            DockerComposeProject.workspace_id == workspace_id,
        ).first()
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Docker Compose project tidak ditemukan.")

        server = project.server
        host, port, username, password, private_key, passphrase = self._extract_credentials(server)
        provider = self._get_provider(server, db)
        res = await provider.execute_compose_action(
            host, port, username, password, private_key, passphrase,
            working_directory=project.working_directory,
            compose_file=project.compose_file,
            project_name=project.project_name,
            action=action,
        )

        status_enum = ComposeProjectStatus.UNKNOWN
        try:
            status_enum = ComposeProjectStatus[res.status]
        except Exception:
            pass

        return DockerComposeActionResult(
            success=res.success,
            project_id=project.id,
            action=res.action,
            status=status_enum,
            message=res.message,
            checked_at=datetime.now(timezone.utc),
        )
