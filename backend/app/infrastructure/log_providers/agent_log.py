import uuid
from typing import List, Optional
from sqlalchemy.orm import Session

from app.infrastructure.log_providers.base import (
    LogProvider,
    LogQueryResult,
    RawLogEntry,
)
from app.services.agent_manager import AgentManager
from app.services.agent_dispatcher import AgentDispatcher, dispatcher_instance, AgentOfflineError


class AgentLogProvider(LogProvider):
    """Service log retrieval provider via outbound DevOps Agent."""

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

    async def get_service_logs(
        self,
        host: str,
        port: int,
        username: str,
        password: Optional[str] = None,
        private_key: Optional[str] = None,
        passphrase: Optional[str] = None,
        service_name: str = "",
        lines: int = 100,
        since: Optional[str] = None,
    ) -> LogQueryResult:
        try:
            agent = self._get_active_agent()
            res = await self.dispatcher.execute_job(
                db=self.db,
                agent=agent,
                operation="GET_SERVICE_LOGS",
                payload={"service_name": service_name, "lines": lines, "since": since},
                timeout_seconds=20,
            )

            entries_raw = res.get("entries", [])
            entries = [
                RawLogEntry(
                    timestamp=None,
                    priority=e.get("priority", "INFO") if isinstance(e, dict) else "INFO",
                    message=e.get("message", "") if isinstance(e, dict) else str(e),
                )
                for e in entries_raw
            ]

            return LogQueryResult(
                service_name=service_name,
                lines_requested=lines,
                lines_returned=len(entries),
                entries=entries,
                truncated=res.get("truncated", False),
            )
        except Exception as e:
            return LogQueryResult(
                service_name=service_name,
                lines_requested=lines,
                lines_returned=0,
                error=str(e),
            )
