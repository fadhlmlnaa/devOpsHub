import uuid
from typing import List, Optional
from sqlalchemy.orm import Session

from app.infrastructure.docker_providers.base import (
    DockerProvider,
    DockerStatusResult,
    ContainerSummaryResult,
    ContainerDetailResult,
    ContainerActionResult,
    ContainerLogsResult,
    ContainerLogEntryResult,
    ComposeStatusResult,
    ComposeActionResult,
    ComposeServiceStatusResult,
)
from app.services.agent_manager import AgentManager
from app.services.agent_dispatcher import AgentDispatcher, dispatcher_instance, AgentOfflineError


class AgentDockerProvider(DockerProvider):
    """Docker management provider via outbound DevOps Agent."""

    def __init__(
        self,
        db: Session,
        workspace_id: uuid.UUID,
        server_id: uuid.UUID,
        agent_manager: Optional[AgentManager] = None,
        dispatcher: Optional[AgentDispatcher] = None,
    ):
        self.db = db
        self.workspace_id = workspace_id
        self.server_id = server_id
        self.agent_manager = agent_manager or AgentManager()
        self.dispatcher = dispatcher or dispatcher_instance

    def _get_active_agent(self):
        agent = self.agent_manager.get_agent_for_server(self.db, self.workspace_id, self.server_id)
        if not agent or not agent.is_active or agent.status != "ONLINE":
            raise AgentOfflineError("DevOps Agent pada server ini sedang offline atau belum terhubung.")
        return agent

    async def get_docker_status(
        self,
        host: str,
        port: int,
        username: str,
        password: Optional[str] = None,
        private_key: Optional[str] = None,
        passphrase: Optional[str] = None,
    ) -> DockerStatusResult:
        try:
            agent = self._get_active_agent()
            res = await self.dispatcher.execute_job(
                db=self.db,
                agent=agent,
                operation="GET_DOCKER_INFO",
                timeout_seconds=15,
            )
            return DockerStatusResult(
                installed=res.get("installed", False),
                running=res.get("running", False),
                version=res.get("version"),
                state=res.get("state", "RUNNING" if res.get("running") else "STOPPED"),
            )
        except Exception as e:
            return DockerStatusResult(
                installed=False,
                running=False,
                state="OFFLINE",
                error=str(e),
            )

    async def list_containers(
        self,
        host: str,
        port: int,
        username: str,
        password: Optional[str] = None,
        private_key: Optional[str] = None,
        passphrase: Optional[str] = None,
        state_filter: str = "running",
    ) -> List[ContainerSummaryResult]:
        try:
            agent = self._get_active_agent()
            res = await self.dispatcher.execute_job(
                db=self.db,
                agent=agent,
                operation="LIST_DOCKER_CONTAINERS",
                payload={"state_filter": state_filter},
                timeout_seconds=15,
            )
            containers_raw = res.get("containers", [])
            return [
                ContainerSummaryResult(
                    id=c.get("id", ""),
                    name=c.get("name", ""),
                    image=c.get("image", ""),
                    status=c.get("status", ""),
                    state=c.get("state", ""),
                    created_at=c.get("created_at"),
                    ports=c.get("ports", []),
                )
                for c in containers_raw
            ]
        except Exception:
            return []

    async def get_container_detail(
        self,
        host: str,
        port: int,
        username: str,
        password: Optional[str] = None,
        private_key: Optional[str] = None,
        passphrase: Optional[str] = None,
        container_id: str = "",
    ) -> Optional[ContainerDetailResult]:
        try:
            agent = self._get_active_agent()
            res = await self.dispatcher.execute_job(
                db=self.db,
                agent=agent,
                operation="GET_DOCKER_CONTAINER",
                payload={"container_id": container_id},
                timeout_seconds=15,
            )
            c = res.get("container")
            if not c:
                return None
            return ContainerDetailResult(
                id=c.get("id", container_id),
                name=c.get("name", ""),
                image=c.get("image", ""),
                state=c.get("state", ""),
                status=c.get("status", ""),
                created_at=c.get("created_at"),
                started_at=c.get("started_at"),
                ports=c.get("ports", []),
                restart_policy=c.get("restart_policy"),
                cpu_usage=c.get("cpu_usage"),
                memory_usage=c.get("memory_usage"),
            )
        except Exception:
            return None

    async def execute_container_action(
        self,
        host: str,
        port: int,
        username: str,
        password: Optional[str] = None,
        private_key: Optional[str] = None,
        passphrase: Optional[str] = None,
        container_id: str = "",
        action: str = "restart",
    ) -> ContainerActionResult:
        op_map = {
            "start": "START_DOCKER_CONTAINER",
            "stop": "STOP_DOCKER_CONTAINER",
            "restart": "RESTART_DOCKER_CONTAINER",
        }
        operation = op_map.get(action.lower(), "RESTART_DOCKER_CONTAINER")
        try:
            agent = self._get_active_agent()
            res = await self.dispatcher.execute_job(
                db=self.db,
                agent=agent,
                operation=operation,
                payload={"container_id": container_id, "action": action},
                timeout_seconds=30,
            )
            return ContainerActionResult(
                success=res.get("success", False),
                container=container_id,
                action=action,
                current_state=res.get("current_state", "unknown"),
                message=res.get("message", f"Aksi {action} container berhasil."),
            )
        except Exception as e:
            return ContainerActionResult(
                success=False,
                container=container_id,
                action=action,
                current_state="unknown",
                message=f"Gagal mengeksekusi aksi container: {str(e)}",
                error=str(e),
            )

    async def get_container_logs(
        self,
        host: str,
        port: int,
        username: str,
        password: Optional[str] = None,
        private_key: Optional[str] = None,
        passphrase: Optional[str] = None,
        container_id: str = "",
        lines: int = 100,
        since: Optional[str] = None,
    ) -> ContainerLogsResult:
        try:
            agent = self._get_active_agent()
            res = await self.dispatcher.execute_job(
                db=self.db,
                agent=agent,
                operation="GET_DOCKER_LOGS",
                payload={"container_id": container_id, "lines": lines, "since": since},
                timeout_seconds=20,
            )
            entries_raw = res.get("entries", [])
            entries = [
                ContainerLogEntryResult(
                    timestamp=None,
                    message=entry if isinstance(entry, str) else entry.get("message", ""),
                )
                for entry in entries_raw
            ]
            return ContainerLogsResult(
                container=container_id,
                lines_requested=lines,
                lines_returned=len(entries),
                entries=entries,
            )
        except Exception as e:
            return ContainerLogsResult(
                container=container_id,
                lines_requested=lines,
                lines_returned=0,
                error=str(e),
            )

    async def get_compose_status(
        self,
        host: str,
        port: int,
        username: str,
        password: Optional[str] = None,
        private_key: Optional[str] = None,
        passphrase: Optional[str] = None,
        working_directory: str = "",
        compose_file: str = "docker-compose.yml",
        project_name: str = "",
    ) -> ComposeStatusResult:
        try:
            agent = self._get_active_agent()
            res = await self.dispatcher.execute_job(
                db=self.db,
                agent=agent,
                operation="GET_DOCKER_INFO",
                payload={
                    "type": "compose",
                    "working_directory": working_directory,
                    "compose_file": compose_file,
                    "project_name": project_name,
                },
                timeout_seconds=20,
            )
            services_raw = res.get("services", [])
            services = [
                ComposeServiceStatusResult(
                    name=s.get("name", ""),
                    service=s.get("service"),
                    state=s.get("state", "unknown"),
                    status=s.get("status"),
                )
                for s in services_raw
            ]
            return ComposeStatusResult(
                project_name=project_name,
                status=res.get("status", "UNKNOWN"),
                services=services,
            )
        except Exception as e:
            return ComposeStatusResult(
                project_name=project_name,
                status="OFFLINE",
                error=str(e),
            )

    async def execute_compose_action(
        self,
        host: str,
        port: int,
        username: str,
        password: Optional[str] = None,
        private_key: Optional[str] = None,
        passphrase: Optional[str] = None,
        working_directory: str = "",
        compose_file: str = "docker-compose.yml",
        project_name: str = "",
        action: str = "restart",
    ) -> ComposeActionResult:
        try:
            agent = self._get_active_agent()
            res = await self.dispatcher.execute_job(
                db=self.db,
                agent=agent,
                operation="GET_DOCKER_INFO",
                payload={
                    "type": "compose_action",
                    "working_directory": working_directory,
                    "compose_file": compose_file,
                    "project_name": project_name,
                    "action": action,
                },
                timeout_seconds=45,
            )
            return ComposeActionResult(
                success=res.get("success", False),
                project_name=project_name,
                action=action,
                status=res.get("status", "RUNNING"),
                message=res.get("message", f"Compose {action} berhasil."),
            )
        except Exception as e:
            return ComposeActionResult(
                success=False,
                project_name=project_name,
                action=action,
                status="FAILED",
                message=f"Gagal menjalankan compose action: {str(e)}",
                error=str(e),
            )
