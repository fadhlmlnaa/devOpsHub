import uuid
from typing import Any, Callable, Dict, List, Optional
from sqlalchemy.orm import Session

from app.infrastructure.deployment_providers.base import (
    DeploymentProvider,
    DeploymentExecutionResult,
)
from app.services.agent_manager import AgentManager
from app.services.agent_dispatcher import AgentDispatcher, dispatcher_instance, AgentOfflineError


class AgentDeploymentProvider(DeploymentProvider):
    """Deployment provider via outbound DevOps Agent."""

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

    async def validate_environment(
        self,
        host: str,
        port: int,
        username: str,
        password: Optional[str] = None,
        private_key: Optional[str] = None,
        passphrase: Optional[str] = None,
        config: Any = None,
    ) -> tuple[bool, str]:
        try:
            agent = self._get_active_agent()
            res = await self.dispatcher.execute_job(
                db=self.db,
                agent=agent,
                operation="DEPLOY",
                payload={"action": "validate", "working_directory": getattr(config, "working_directory", "")},
                timeout_seconds=15,
            )
            return res.get("valid", True), res.get("message", "Environment valid.")
        except Exception as e:
            return False, str(e)

    async def deploy(
        self,
        host: str,
        port: int,
        username: str,
        password: Optional[str] = None,
        private_key: Optional[str] = None,
        passphrase: Optional[str] = None,
        config: Any = None,
        log_callback: Optional[Callable[[str, str], Any]] = None,
    ) -> DeploymentExecutionResult:
        try:
            agent = self._get_active_agent()
            config_payload = {
                "action": "execute",
                "repository_url": getattr(config, "repository_url", None),
                "branch": getattr(config, "branch", "main"),
                "working_directory": getattr(config, "working_directory", ""),
                "build_command": getattr(config, "build_command", None),
                "restart_service": getattr(config, "restart_service", None),
                "health_check_endpoint": getattr(config, "health_check_endpoint", None),
                "timeout_seconds": getattr(config, "timeout_seconds", 300),
            }

            timeout = getattr(config, "timeout_seconds", 300) + 30
            res = await self.dispatcher.execute_job(
                db=self.db,
                agent=agent,
                operation="DEPLOY",
                payload=config_payload,
                timeout_seconds=timeout,
            )

            logs = res.get("logs", [])
            if log_callback:
                for log_item in logs:
                    log_callback(log_item.get("level", "INFO"), log_item.get("message", ""))

            return DeploymentExecutionResult(
                success=res.get("success", False),
                status=res.get("status", "SUCCESS" if res.get("success") else "FAILED"),
                commit_reference=res.get("commit_reference"),
                message=res.get("message", "Deployment selesai."),
                error_message=res.get("error_message"),
                logs=logs,
            )
        except Exception as e:
            return DeploymentExecutionResult(
                success=False,
                status="FAILED",
                message=f"Deployment via Agent gagal: {str(e)}",
                error_message=str(e),
                logs=[{"level": "ERROR", "message": str(e)}],
            )
