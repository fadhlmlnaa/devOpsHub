from typing import Optional
from sqlalchemy.orm import Session

from app.models.server import Server

from app.infrastructure.service_providers.base import ServiceProvider
from app.infrastructure.service_providers.ssh_systemd import SSHSystemdProvider
from app.infrastructure.service_providers.agent_systemd import AgentSystemdProvider

from app.infrastructure.docker_providers.base import DockerProvider
from app.infrastructure.docker_providers.ssh_docker import SSHDockerProvider
from app.infrastructure.docker_providers.agent_docker import AgentDockerProvider

from app.infrastructure.deployment_providers.base import DeploymentProvider
from app.infrastructure.deployment_providers.ssh_deployment import SSHDeploymentProvider
from app.infrastructure.deployment_providers.agent_deployment import AgentDeploymentProvider

from app.infrastructure.backup_providers.base import BackupProvider
from app.infrastructure.backup_providers.ssh_backup import SSHBackupProvider
from app.infrastructure.backup_providers.agent_backup import AgentBackupProvider

from app.infrastructure.log_providers.base import LogProvider
from app.infrastructure.log_providers.ssh_journal import SSHJournalLogProvider
from app.infrastructure.log_providers.agent_log import AgentLogProvider


class ProviderFactory:
    """Factory to resolve appropriate Execution/Transport Provider based on server connection_type."""

    @staticmethod
    def get_service_provider(server: Server, db: Optional[Session] = None) -> ServiceProvider:
        if server.connection_type == "AGENT" and db is not None:
            return AgentSystemdProvider(
                db=db,
                workspace_id=server.workspace_id,
                server_id=server.id,
            )
        return SSHSystemdProvider()

    @staticmethod
    def get_docker_provider(server: Server, db: Optional[Session] = None) -> DockerProvider:
        if server.connection_type == "AGENT" and db is not None:
            return AgentDockerProvider(
                db=db,
                workspace_id=server.workspace_id,
                server_id=server.id,
            )
        return SSHDockerProvider()

    @staticmethod
    def get_deployment_provider(server: Server, db: Optional[Session] = None) -> DeploymentProvider:
        if server.connection_type == "AGENT" and db is not None:
            return AgentDeploymentProvider(
                db=db,
                workspace_id=server.workspace_id,
                server_id=server.id,
            )
        return SSHDeploymentProvider()

    @staticmethod
    def get_backup_provider(server: Server, db: Optional[Session] = None) -> BackupProvider:
        if server.connection_type == "AGENT" and db is not None:
            return AgentBackupProvider(
                db=db,
                workspace_id=server.workspace_id,
                server_id=server.id,
            )
        return SSHBackupProvider()

    @staticmethod
    def get_log_provider(server: Server, db: Optional[Session] = None) -> LogProvider:
        if server.connection_type == "AGENT" and db is not None:
            return AgentLogProvider(
                db=db,
                workspace_id=server.workspace_id,
                server_id=server.id,
            )
        return SSHJournalLogProvider()
