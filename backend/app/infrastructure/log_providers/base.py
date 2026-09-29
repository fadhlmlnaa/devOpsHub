from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class RawLogEntry:
    timestamp: Optional[datetime] = None
    priority: str = "INFO"
    message: str = ""


@dataclass
class LogQueryResult:
    service_name: str
    lines_requested: int
    lines_returned: int
    truncated: bool = False
    entries: List[RawLogEntry] = field(default_factory=list)
    error: Optional[str] = None
    systemd_supported: bool = True


class LogProvider(ABC):
    """Abstract interface for service log retrieval provider."""

    @abstractmethod
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
        """Fetch systemd journal logs for a service."""
        pass
