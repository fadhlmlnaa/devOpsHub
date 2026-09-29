from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID


class NotificationProvider(ABC):
    """Abstract interface for sending alerts and notifications."""

    @abstractmethod
    async def send(
        self,
        user_id: UUID,
        workspace_id: UUID,
        title: str,
        message: str,
        severity: str,
        alert_id: Optional[UUID] = None,
    ) -> bool:
        """Send a notification to a specific user."""
        pass
