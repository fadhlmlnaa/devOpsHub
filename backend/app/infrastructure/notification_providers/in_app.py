import logging
from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session

from app.models.alert import Notification
from app.infrastructure.notification_providers.base import NotificationProvider

logger = logging.getLogger(__name__)


class InAppNotificationProvider(NotificationProvider):
    """In-App notification provider that stores records in the database."""

    def __init__(self, db: Session):
        self.db = db

    async def send(
        self,
        user_id: UUID,
        workspace_id: UUID,
        title: str,
        message: str,
        severity: str,
        alert_id: Optional[UUID] = None,
    ) -> bool:
        try:
            notification = Notification(
                user_id=user_id,
                workspace_id=workspace_id,
                alert_id=alert_id,
                title=title,
                message=message,
                severity=severity,
                is_read=False,
            )
            self.db.add(notification)
            self.db.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to create in-app notification: {e}")
            self.db.rollback()
            return False
