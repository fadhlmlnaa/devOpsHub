import logging
from typing import Optional
from uuid import UUID

from app.infrastructure.notification_providers.base import NotificationProvider

logger = logging.getLogger(__name__)


class EmailNotificationProvider(NotificationProvider):
    """Email notification provider stub/logger."""

    async def send(
        self,
        user_id: UUID,
        workspace_id: UUID,
        title: str,
        message: str,
        severity: str,
        alert_id: Optional[UUID] = None,
    ) -> bool:
        logger.info(
            f"[EMAIL NOTIFICATION STUB] To user {user_id} (workspace {workspace_id}): "
            f"[{severity}] {title} - {message}"
        )
        return True
