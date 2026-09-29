import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import delete

from app.core.config import settings
from app.models.audit_log import AuditLog
from app.models.agent import AgentJob
from app.models.alert import AlertEvent
from app.models.deployment import Deployment
from app.models.backup import BackupExecutionLog

logger = logging.getLogger(__name__)


class MaintenanceService:
    """Service to safely clean up expired audit logs, job records, and historical events."""

    def __init__(self, db: Session):
        self.db = db

    def cleanup_expired_records(self) -> Dict[str, Any]:
        """Deletes historical logs older than configured retention policies."""
        now = datetime.now(timezone.utc)
        audit_threshold = now - timedelta(days=settings.AUDIT_RETENTION_DAYS)
        job_threshold = now - timedelta(days=settings.JOB_RETENTION_DAYS)

        summary = {
            "cleaned_at": now.isoformat(),
            "audit_logs_deleted": 0,
            "agent_jobs_deleted": 0,
            "alert_events_deleted": 0,
        }

        try:
            # 1. Audit Logs Cleanup
            stmt_audit = delete(AuditLog).where(AuditLog.created_at < audit_threshold)
            res_audit = self.db.execute(stmt_audit)
            summary["audit_logs_deleted"] = res_audit.rowcount or 0

            # 2. Agent Jobs Cleanup (Only terminal statuses: COMPLETED, FAILED, TIMED_OUT)
            stmt_jobs = delete(AgentJob).where(
                AgentJob.created_at < job_threshold,
                AgentJob.status.in_(["COMPLETED", "FAILED", "TIMED_OUT", "CANCELLED"]),
            )
            res_jobs = self.db.execute(stmt_jobs)
            summary["agent_jobs_deleted"] = res_jobs.rowcount or 0

            # 3. Alert Events Cleanup (Resolved alerts older than retention)
            stmt_alerts = delete(AlertEvent).where(
                AlertEvent.created_at < audit_threshold,
                AlertEvent.status == "RESOLVED",
            )
            res_alerts = self.db.execute(stmt_alerts)
            summary["alert_events_deleted"] = res_alerts.rowcount or 0

            self.db.commit()
            if any(summary[k] > 0 for k in ["audit_logs_deleted", "agent_jobs_deleted", "alert_events_deleted"]):
                logger.info(f"Maintenance retention cleanup completed: {summary}")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Maintenance retention cleanup failed: {e}", exc_info=True)
            summary["error"] = str(e)

        return summary
