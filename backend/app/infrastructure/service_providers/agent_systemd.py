import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from app.infrastructure.service_providers.base import (
    ServiceProvider,
    ServiceInfo,
    ServiceListResult,
    ServiceActionResult,
)
from app.services.agent_manager import AgentManager
from app.services.agent_dispatcher import AgentDispatcher, dispatcher_instance, AgentOfflineError


class AgentSystemdProvider(ServiceProvider):
    """Systemd service management provider via outbound DevOps Agent."""

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

    async def is_systemd_supported(
        self,
        host: str,
        port: int,
        username: str,
        password: Optional[str] = None,
        private_key: Optional[str] = None,
        passphrase: Optional[str] = None,
    ) -> bool:
        try:
            agent = self._get_active_agent()
            caps = agent.capabilities or {}
            if "systemd" in caps:
                return bool(caps.get("systemd"))
            return True
        except Exception:
            return False

    async def list_services(
        self,
        host: str,
        port: int,
        username: str,
        password: Optional[str] = None,
        private_key: Optional[str] = None,
        passphrase: Optional[str] = None,
        state: Optional[str] = None,
        limit: int = 100,
    ) -> ServiceListResult:
        try:
            agent = self._get_active_agent()
            res = await self.dispatcher.execute_job(
                db=self.db,
                agent=agent,
                operation="GET_SERVICE_STATUS",
                payload={"action": "list", "state": state, "limit": limit},
                timeout_seconds=15,
            )

            services_raw = res.get("services", [])
            services = [
                ServiceInfo(
                    name=s.get("name", ""),
                    load_state=s.get("load_state", "unknown"),
                    active_state=s.get("active_state", "unknown"),
                    sub_state=s.get("sub_state", "unknown"),
                    description=s.get("description"),
                    enabled=s.get("enabled"),
                    main_pid=s.get("main_pid"),
                    active_enter_timestamp=s.get("active_enter_timestamp"),
                )
                for s in services_raw
            ]
            return ServiceListResult(systemd_supported=True, services=services)
        except Exception as e:
            return ServiceListResult(systemd_supported=False, services=[], error_message=str(e))

    async def get_service(
        self,
        host: str,
        port: int,
        username: str,
        password: Optional[str] = None,
        private_key: Optional[str] = None,
        passphrase: Optional[str] = None,
        service_name: str = "",
    ) -> Optional[ServiceInfo]:
        try:
            agent = self._get_active_agent()
            res = await self.dispatcher.execute_job(
                db=self.db,
                agent=agent,
                operation="GET_SERVICE_STATUS",
                payload={"service_name": service_name},
                timeout_seconds=15,
            )

            service_data = res.get("service")
            if not service_data:
                return None

            return ServiceInfo(
                name=service_data.get("name", service_name),
                load_state=service_data.get("load_state", "unknown"),
                active_state=service_data.get("active_state", "unknown"),
                sub_state=service_data.get("sub_state", "unknown"),
                description=service_data.get("description"),
                enabled=service_data.get("enabled"),
                main_pid=service_data.get("main_pid"),
                active_enter_timestamp=service_data.get("active_enter_timestamp"),
            )
        except Exception:
            return None

    async def execute_action(
        self,
        host: str,
        port: int,
        username: str,
        password: Optional[str] = None,
        private_key: Optional[str] = None,
        passphrase: Optional[str] = None,
        service_name: str = "",
        action: str = "",
    ) -> ServiceActionResult:
        op_map = {
            "start": "START_SERVICE",
            "stop": "STOP_SERVICE",
            "restart": "RESTART_SERVICE",
            "reload": "RELOAD_SERVICE",
        }
        operation = op_map.get(action.lower())
        if not operation:
            return ServiceActionResult(
                success=False,
                service=service_name,
                action=action,
                message=f"Aksi service '{action}' tidak valid.",
                error="INVALID_ACTION",
            )

        try:
            agent = self._get_active_agent()
            res = await self.dispatcher.execute_job(
                db=self.db,
                agent=agent,
                operation=operation,
                payload={"service_name": service_name, "action": action},
                timeout_seconds=30,
            )

            return ServiceActionResult(
                success=res.get("success", False),
                service=service_name,
                action=action,
                previous_state=res.get("previous_state"),
                current_state=res.get("current_state"),
                message=res.get("message", f"Aksi {action} pada {service_name} berhasil."),
            )
        except AgentOfflineError as e:
            return ServiceActionResult(
                success=False,
                service=service_name,
                action=action,
                message=str(e),
                error="AGENT_OFFLINE",
            )
        except Exception as e:
            return ServiceActionResult(
                success=False,
                service=service_name,
                action=action,
                message=f"Gagal menjalankan {action} pada service {service_name}: {str(e)}",
                error="EXECUTION_ERROR",
            )
