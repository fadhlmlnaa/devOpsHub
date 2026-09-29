import uuid
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional
from sqlalchemy.orm import Session

from app.infrastructure.backup_providers.base import (
    BackupProvider,
    BackupExecutionResult,
    BackupVerificationResult,
)
from app.services.agent_manager import AgentManager
from app.services.agent_dispatcher import AgentDispatcher, dispatcher_instance, AgentOfflineError


class AgentBackupProvider(BackupProvider):
    """Backup execution and verification provider via outbound DevOps Agent."""

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
                operation="BACKUP",
                payload={"action": "validate", "destination_path": getattr(config, "destination_path", "")},
                timeout_seconds=15,
            )
            return res.get("valid", True), res.get("message", "Target backup valid.")
        except Exception as e:
            return False, str(e)

    async def execute(
        self,
        host: str,
        port: int,
        username: str,
        password: Optional[str] = None,
        private_key: Optional[str] = None,
        passphrase: Optional[str] = None,
        config: Any = None,
        log_callback: Optional[Callable[[str, str, int, datetime], Any]] = None,
    ) -> BackupExecutionResult:
        try:
            agent = self._get_active_agent()
            config_payload = {
                "action": "execute",
                "backup_type": getattr(config, "backup_type", "DIRECTORY"),
                "source_path": getattr(config, "source_path", None),
                "destination_path": getattr(config, "destination_path", ""),
                "db_name": getattr(config, "db_name", None),
                "db_user": getattr(config, "db_user", None),
                "is_compressed": getattr(config, "is_compressed", True),
                "retention_days": getattr(config, "retention_days", 7),
            }

            res = await self.dispatcher.execute_job(
                db=self.db,
                agent=agent,
                operation="BACKUP",
                payload=config_payload,
                timeout_seconds=300,
            )

            logs = res.get("logs", [])
            if log_callback:
                for idx, log_item in enumerate(logs, start=1):
                    log_callback(
                        log_item.get("level", "INFO"),
                        log_item.get("message", ""),
                        idx,
                        datetime.utcnow(),
                    )

            return BackupExecutionResult(
                success=res.get("success", False),
                status=res.get("status", "SUCCESS" if res.get("success") else "FAILED"),
                file_name=res.get("file_name"),
                file_path=res.get("file_path"),
                file_size_bytes=res.get("file_size_bytes"),
                checksum=res.get("checksum"),
                error_message=res.get("error_message"),
                logs=logs,
            )
        except Exception as e:
            return BackupExecutionResult(
                success=False,
                status="FAILED",
                error_message=f"Backup via Agent gagal: {str(e)}",
                logs=[{"level": "ERROR", "message": str(e)}],
            )

    async def verify(
        self,
        host: str,
        port: int,
        username: str,
        password: Optional[str] = None,
        private_key: Optional[str] = None,
        passphrase: Optional[str] = None,
        file_path: str = "",
        expected_checksum: Optional[str] = None,
    ) -> BackupVerificationResult:
        try:
            agent = self._get_active_agent()
            res = await self.dispatcher.execute_job(
                db=self.db,
                agent=agent,
                operation="BACKUP",
                payload={
                    "action": "verify",
                    "file_path": file_path,
                    "expected_checksum": expected_checksum,
                },
                timeout_seconds=30,
            )
            return BackupVerificationResult(
                verified=res.get("verified", False),
                file_exists=res.get("file_exists", False),
                stored_checksum=expected_checksum,
                calculated_checksum=res.get("calculated_checksum"),
                message=res.get("message", "Verifikasi backup selesai."),
            )
        except Exception as e:
            return BackupVerificationResult(
                verified=False,
                file_exists=False,
                stored_checksum=expected_checksum,
                message=f"Gagal verifikasi backup via Agent: {str(e)}",
            )
