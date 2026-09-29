import uuid
import json
import secrets
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional
from fastapi import WebSocket
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.agent import Agent, AgentJob
from app.services.redaction import SecretRedactor


class AgentOfflineError(Exception):
    """Raised when an operation is requested on an offline or disconnected agent."""
    pass


class AgentJobError(Exception):
    """Raised when an agent job fails or returns an error."""
    pass


class AgentDispatcher:
    ALLOWED_OPERATIONS = {
        "GET_SYSTEM_METRICS",
        "GET_SERVER_INFO",
        "GET_SERVICE_STATUS",
        "START_SERVICE",
        "STOP_SERVICE",
        "RESTART_SERVICE",
        "RELOAD_SERVICE",
        "GET_SERVICE_LOGS",
        "GET_DOCKER_INFO",
        "LIST_DOCKER_CONTAINERS",
        "GET_DOCKER_CONTAINER",
        "START_DOCKER_CONTAINER",
        "STOP_DOCKER_CONTAINER",
        "RESTART_DOCKER_CONTAINER",
        "GET_DOCKER_LOGS",
        "DEPLOY",
        "BACKUP",
    }

    def __init__(self):
        # agent_id (str) -> WebSocket
        self._connections: Dict[str, WebSocket] = {}
        # nonce (str) -> asyncio.Future
        self._pending_futures: Dict[str, asyncio.Future] = {}
        self._lock = asyncio.Lock()

    async def register_connection(self, agent_id: uuid.UUID, websocket: WebSocket) -> None:
        async with self._lock:
            self._connections[str(agent_id)] = websocket

    async def unregister_connection(self, agent_id: uuid.UUID, websocket: Optional[WebSocket] = None) -> None:
        async with self._lock:
            key = str(agent_id)
            if key in self._connections:
                if websocket is None or self._connections[key] == websocket:
                    del self._connections[key]

    def is_connected(self, agent_id: uuid.UUID) -> bool:
        return str(agent_id) in self._connections

    async def handle_agent_message(self, agent_id: uuid.UUID, message_data: Dict[str, Any]) -> None:
        msg_type = message_data.get("type")

        if msg_type == "JOB_RESULT":
            nonce = message_data.get("nonce")
            if nonce and nonce in self._pending_futures:
                fut = self._pending_futures[nonce]
                if not fut.done():
                    fut.set_result(message_data)

    async def execute_job(
        self,
        db: Session,
        agent: Agent,
        operation: str,
        payload: Optional[Dict[str, Any]] = None,
        timeout_seconds: int = 30,
        request_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        if operation not in self.ALLOWED_OPERATIONS:
            raise ValueError(f"Operasi '{operation}' tidak diizinkan dalam agent operation allowlist.")

        if not agent.is_active or agent.status == "DISABLED":
            raise AgentOfflineError(f"Agent {agent.id} berada dalam status DISABLED.")

        agent_id_str = str(agent.id)
        ws = self._connections.get(agent_id_str)

        if not ws:
            raise AgentOfflineError(f"Agent {agent.name} ({agent.id}) sedang offline / tidak terhubung.")

        now = datetime.now(timezone.utc)
        nonce = secrets.token_hex(16)
        expires_at = now + timedelta(seconds=timeout_seconds)

        # Sanitize sensitive fields before saving payload to DB
        safe_payload = SecretRedactor.redact_dict(payload) if payload else {}

        # Create AgentJob record
        job = AgentJob(
            agent_id=agent.id,
            workspace_id=agent.workspace_id,
            server_id=agent.server_id,
            operation=operation,
            status="RUNNING",
            request_id=request_id,
            payload=safe_payload,
            nonce=nonce,
            timeout_seconds=timeout_seconds,
            created_at=now,
            started_at=now,
            expires_at=expires_at,
        )
        db.add(job)
        db.commit()
        db.refresh(job)

        # Setup Future for response matching
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        self._pending_futures[nonce] = future

        message = {
            "type": "JOB_REQUEST",
            "job_id": str(job.id),
            "operation": operation,
            "payload": payload or {},
            "nonce": nonce,
            "timeout_seconds": timeout_seconds,
            "expires_at": expires_at.isoformat(),
        }

        try:
            await ws.send_text(json.dumps(message))

            # Await result with timeout
            result_data = await asyncio.wait_for(future, timeout=float(timeout_seconds))

            finished_at = datetime.now(timezone.utc)
            status = result_data.get("status", "FAILED")
            result_body = result_data.get("result")
            error_cat = result_data.get("error_category")
            error_msg = result_data.get("error_message")

            safe_result = SecretRedactor.redact_dict(result_body) if isinstance(result_body, dict) else result_body

            job.status = "SUCCESS" if status == "SUCCESS" else "FAILED"
            job.result = safe_result if isinstance(safe_result, dict) else {"output": safe_result}
            job.error_category = error_cat
            job.error_message = error_msg
            job.finished_at = finished_at

            db.commit()

            if status != "SUCCESS":
                raise AgentJobError(error_msg or f"Agent job {operation} gagal dieksekusi.")

            return result_body or {}

        except asyncio.TimeoutError:
            job.status = "EXPIRED"
            job.error_category = "TIMEOUT"
            job.error_message = f"Job timeout setelah {timeout_seconds} detik."
            job.finished_at = datetime.now(timezone.utc)
            db.commit()
            raise AgentJobError(f"Operasi {operation} melebihi batas waktu ({timeout_seconds}s).")

        except Exception as e:
            if not isinstance(e, (AgentJobError, AgentOfflineError)):
                job.status = "FAILED"
                job.error_category = "DISPATCH_ERROR"
                job.error_message = str(e)
                job.finished_at = datetime.now(timezone.utc)
                db.commit()
            raise

        finally:
            self._pending_futures.pop(nonce, None)


# Global Singleton Dispatcher instance
dispatcher_instance = AgentDispatcher()
