import logging
from datetime import datetime
from typing import List, Optional, Tuple
from uuid import UUID
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.alert import (
    Notification,
    NotificationPreference,
    Alert,
    AlertEvent,
)
from app.models.workspace_member import WorkspaceMember
from app.infrastructure.notification_providers.in_app import InAppNotificationProvider
from app.infrastructure.notification_providers.email import EmailNotificationProvider
from app.services.redaction import SecretRedactor

logger = logging.getLogger(__name__)

SEVERITY_WEIGHT = {
    "INFO": 1,
    "WARNING": 2,
    "CRITICAL": 3,
}


class NotificationService:
    def __init__(self, db: Session):
        self.db = db
        self.in_app_provider = InAppNotificationProvider(db)
        self.email_provider = EmailNotificationProvider()
        self.redactor = SecretRedactor()

    def get_or_create_preference(
        self, user_id: UUID, workspace_id: UUID
    ) -> NotificationPreference:
        pref = (
            self.db.query(NotificationPreference)
            .filter(
                NotificationPreference.user_id == user_id,
                NotificationPreference.workspace_id == workspace_id,
            )
            .first()
        )
        if not pref:
            pref = NotificationPreference(
                user_id=user_id,
                workspace_id=workspace_id,
                in_app_enabled=True,
                email_enabled=False,
                minimum_severity="INFO",
            )
            self.db.add(pref)
            self.db.commit()
            self.db.refresh(pref)
        return pref

    def update_preference(
        self,
        user_id: UUID,
        workspace_id: UUID,
        in_app_enabled: Optional[bool] = None,
        email_enabled: Optional[bool] = None,
        minimum_severity: Optional[str] = None,
    ) -> NotificationPreference:
        pref = self.get_or_create_preference(user_id, workspace_id)
        if in_app_enabled is not None:
            pref.in_app_enabled = in_app_enabled
        if email_enabled is not None:
            pref.email_enabled = email_enabled
        if minimum_severity is not None:
            pref.minimum_severity = minimum_severity.upper()

        pref.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(pref)
        return pref

    def get_user_notifications(
        self,
        user_id: UUID,
        workspace_id: UUID,
        unread_only: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Notification]:
        limit = min(max(1, limit), 100)
        query = self.db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.workspace_id == workspace_id,
        )
        if unread_only:
            query = query.filter(Notification.is_read == False)

        return (
            query.order_by(Notification.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    def get_unread_count(self, user_id: UUID, workspace_id: UUID) -> int:
        return (
            self.db.query(func.count(Notification.id))
            .filter(
                Notification.user_id == user_id,
                Notification.workspace_id == workspace_id,
                Notification.is_read == False,
            )
            .scalar()
            or 0
        )

    def mark_as_read(
        self, notification_id: UUID, user_id: UUID, workspace_id: UUID
    ) -> Notification:
        notif = (
            self.db.query(Notification)
            .filter(
                Notification.id == notification_id,
                Notification.user_id == user_id,
                Notification.workspace_id == workspace_id,
            )
            .first()
        )
        if not notif:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notifikasi tidak ditemukan.",
            )

        if not notif.is_read:
            notif.is_read = True
            notif.read_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(notif)
        return notif

    def mark_all_as_read(self, user_id: UUID, workspace_id: UUID) -> int:
        updated_count = (
            self.db.query(Notification)
            .filter(
                Notification.user_id == user_id,
                Notification.workspace_id == workspace_id,
                Notification.is_read == False,
            )
            .update(
                {"is_read": True, "read_at": datetime.utcnow()},
                synchronize_session="fetch",
            )
        )
        self.db.commit()
        return updated_count

    async def dispatch_alert_notification(
        self, alert: Alert, is_resolution: bool = False
    ) -> int:
        """
        Dispatches alert notifications to workspace members who have opted-in
        and whose minimum_severity threshold is met.
        """
        members = (
            self.db.query(WorkspaceMember)
            .filter(WorkspaceMember.workspace_id == alert.workspace_id)
            .all()
        )

        sent_count = 0
        target_severity = alert.severity.upper()
        alert_weight = SEVERITY_WEIGHT.get(target_severity, 1)

        title = f"[RESOLVED] {alert.title}" if is_resolution else f"[{target_severity}] {alert.title}"
        message = (
            f"Kondisi peringatan telah pulih: {alert.message}"
            if is_resolution
            else alert.message
        )

        # Redact secrets before sending notifications
        clean_title = self.redactor.redact(title)
        clean_message = self.redactor.redact(message)

        for member in members:
            pref = self.get_or_create_preference(member.user_id, alert.workspace_id)
            min_weight = SEVERITY_WEIGHT.get(pref.minimum_severity.upper(), 1)

            # Skip if severity is below user's minimum preference
            if alert_weight < min_weight:
                continue

            if pref.in_app_enabled:
                success = await self.in_app_provider.send(
                    user_id=member.user_id,
                    workspace_id=alert.workspace_id,
                    title=clean_title,
                    message=clean_message,
                    severity=target_severity,
                    alert_id=alert.id,
                )
                if success:
                    sent_count += 1

            if pref.email_enabled:
                await self.email_provider.send(
                    user_id=member.user_id,
                    workspace_id=alert.workspace_id,
                    title=clean_title,
                    message=clean_message,
                    severity=target_severity,
                    alert_id=alert.id,
                )

        return sent_count
