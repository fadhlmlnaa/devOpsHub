import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Set
from agent.operations import OPERATIONS_REGISTRY

logger = logging.getLogger(__name__)


class AgentLocalDispatcher:
    """Validates incoming jobs, performs replay protection, and delegates to predefined operations."""

    def __init__(self):
        self._processed_nonces: Set[str] = set()

    def handle_job(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        job_id = job_data.get("job_id")
        operation = job_data.get("operation")
        payload = job_data.get("payload", {})
        nonce = job_data.get("nonce")
        expires_at_str = job_data.get("expires_at")

        # 1. Nonce / Replay check
        if not nonce:
            return {
                "type": "JOB_RESULT",
                "job_id": job_id,
                "nonce": nonce,
                "status": "FAILED",
                "error_category": "INVALID_JOB",
                "error_message": "Missing job nonce.",
            }

        if nonce in self._processed_nonces:
            return {
                "type": "JOB_RESULT",
                "job_id": job_id,
                "nonce": nonce,
                "status": "FAILED",
                "error_category": "DUPLICATE_JOB",
                "error_message": "Duplicate job execution rejected (Replay protection).",
            }

        # 2. Expiration check
        if expires_at_str:
            try:
                expires_at = datetime.fromisoformat(expires_at_str.replace("Z", "+00:00"))
                if expires_at < datetime.now(timezone.utc):
                    return {
                        "type": "JOB_RESULT",
                        "job_id": job_id,
                        "nonce": nonce,
                        "status": "FAILED",
                        "error_category": "EXPIRED_JOB",
                        "error_message": "Job has expired.",
                    }
            except Exception:
                pass

        # 3. Allowlist validation
        handler = OPERATIONS_REGISTRY.get(operation)
        if not handler:
            return {
                "type": "JOB_RESULT",
                "job_id": job_id,
                "nonce": nonce,
                "status": "FAILED",
                "error_category": "UNKNOWN_OPERATION",
                "error_message": f"Operasi '{operation}' tidak diizinkan atau tidak dikenal oleh Agent.",
            }

        # 4. Execute operation
        self._processed_nonces.add(nonce)
        # Limit cache size to 10,000 nonces
        if len(self._processed_nonces) > 10000:
            self._processed_nonces.clear()

        try:
            logger.info("Executing agent job %s (operation: %s)", job_id, operation)
            result = handler(payload)
            return {
                "type": "JOB_RESULT",
                "job_id": job_id,
                "nonce": nonce,
                "status": "SUCCESS",
                "result": result,
            }
        except Exception as e:
            logger.error("Job %s execution failed: %s", job_id, e)
            return {
                "type": "JOB_RESULT",
                "job_id": job_id,
                "nonce": nonce,
                "status": "FAILED",
                "error_category": "EXECUTION_ERROR",
                "error_message": str(e),
            }
