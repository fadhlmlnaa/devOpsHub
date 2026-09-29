import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union
from fastapi import Request
from sqlalchemy import desc
from sqlalchemy.orm import Session, joinedload

from app.core.config import settings
from app.models.audit_log import AuditLog
from app.schemas.audit_log import AuditAction, AuditStatus
from app.services.redaction import SecretRedactor

logger = logging.getLogger(__name__)


class AuditService:
    """Centralized service for recording and retrieving append-only audit logs."""

    def __init__(self, db: Session):
        self.db = db

    def log(
        self,
        action: Union[AuditAction, str],
        resource_type: str,
        status: Union[AuditStatus, str] = AuditStatus.SUCCESS,
        workspace_id: Optional[uuid.UUID] = None,
        user_id: Optional[uuid.UUID] = None,
        resource_id: Optional[str] = None,
        environment_id: Optional[uuid.UUID] = None,
        server_id: Optional[uuid.UUID] = None,
        metadata: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request: Optional[Request] = None,
        commit: bool = True,
    ) -> Optional[AuditLog]:
        """Creates an audit log entry with automatic secret redaction."""
        if not getattr(settings, "AUDIT_LOG_ENABLED", True):
            return None

        # Extract client information from Request if provided and not explicitly set
        if request is not None:
            if not ip_address:
                # Check X-Forwarded-For first
                forwarded = request.headers.get("x-forwarded-for")
                if forwarded:
                    ip_address = forwarded.split(",")[0].strip()
                elif request.client:
                    ip_address = request.client.host
            if not user_agent:
                user_agent = request.headers.get("user-agent")

        # Sanitize metadata
        sanitized_meta: Optional[Dict[str, Any]] = None
        if metadata is not None:
            try:
                sanitized_meta = SecretRedactor.redact_dict(metadata)
            except Exception as e:
                logger.warning(f"Gagal melakukan redaksi metadata audit log: {e}")
                sanitized_meta = {"redaction_error": True}

        action_str = action.value if isinstance(action, AuditAction) else str(action)
        status_str = status.value if isinstance(status, AuditStatus) else str(status)

        try:
            audit_entry = AuditLog(
                workspace_id=workspace_id,
                user_id=user_id,
                action=action_str,
                resource_type=resource_type,
                resource_id=str(resource_id) if resource_id else None,
                environment_id=environment_id,
                server_id=server_id,
                status=status_str,
                ip_address=ip_address[:64] if ip_address else None,
                user_agent=user_agent[:500] if user_agent else None,
                meta_data=sanitized_meta,
            )
            self.db.add(audit_entry)
            if commit:
                self.db.commit()
                self.db.refresh(audit_entry)
            return audit_entry
        except Exception as e:
            logger.error(f"Gagal mencatat audit log [{action_str}]: {e}")
            if commit:
                self.db.rollback()
            return None

    def get_logs(
        self,
        workspace_id: uuid.UUID,
        action: Optional[str] = None,
        status: Optional[str] = None,
        user_id: Optional[uuid.UUID] = None,
        resource_type: Optional[str] = None,
        server_id: Optional[uuid.UUID] = None,
        environment_id: Optional[uuid.UUID] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[AuditLog], int]:
        """Fetch paginated audit logs for a workspace with filters."""
        # Bound limit between 1 and AUDIT_MAX_LIMIT
        max_limit = getattr(settings, "AUDIT_MAX_LIMIT", 100)
        limit = max(1, min(limit, max_limit))
        offset = max(0, offset)

        query = self.db.query(AuditLog).options(joinedload(AuditLog.user)).filter(
            AuditLog.workspace_id == workspace_id
        )

        if action:
            query = query.filter(AuditLog.action == action)
        if status:
            query = query.filter(AuditLog.status == status)
        if user_id:
            query = query.filter(AuditLog.user_id == user_id)
        if resource_type:
            query = query.filter(AuditLog.resource_type == resource_type)
        if server_id:
            query = query.filter(AuditLog.server_id == server_id)
        if environment_id:
            query = query.filter(AuditLog.environment_id == environment_id)
        if start_date:
            query = query.filter(AuditLog.created_at >= start_date)
        if end_date:
            query = query.filter(AuditLog.created_at <= end_date)

        total = query.count()
        items = query.order_by(desc(AuditLog.created_at)).offset(offset).limit(limit).all()

        return items, total
