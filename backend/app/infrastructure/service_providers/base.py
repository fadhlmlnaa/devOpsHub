from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ServiceInfo:
    name: str
    load_state: str
    active_state: str
    sub_state: str
    description: Optional[str] = None
    enabled: Optional[bool] = None
    main_pid: Optional[int] = None
    active_enter_timestamp: Optional[str] = None


@dataclass
class ServiceListResult:
    systemd_supported: bool
    services: List[ServiceInfo] = field(default_factory=list)
    error_message: Optional[str] = None


@dataclass
class ServiceActionResult:
    success: bool
    service: str
    action: str
    previous_state: Optional[Dict[str, Any]] = None
    current_state: Optional[Dict[str, Any]] = None
    message: str = ""
    error: Optional[str] = None


class ServiceProvider(ABC):
    """Abstract interface for Linux service management provider."""

    @abstractmethod
    async def is_systemd_supported(
        self,
        host: str,
        port: int,
        username: str,
        password: Optional[str] = None,
        private_key: Optional[str] = None,
        passphrase: Optional[str] = None,
    ) -> bool:
        """Check if systemd is supported and running on the target server."""
        pass

    @abstractmethod
    async def list_services(
        self,
        host: str,
        port: int,
        username: str,
        password: Optional[str] = None,
        private_key: Optional[str] = None,
        passphrase: Optional[str] = None,
        state: Optional[str] = None,
        limit: int = 100,
    ) -> ServiceListResult:
        """List systemd services on the remote server with optional state filtering."""
        pass

    @abstractmethod
    async def get_service(
        self,
        host: str,
        port: int,
        username: str,
        password: Optional[str] = None,
        private_key: Optional[str] = None,
        passphrase: Optional[str] = None,
        service_name: str = "",
    ) -> Optional[ServiceInfo]:
        """Fetch detailed status of a specific systemd service."""
        pass

    @abstractmethod
    async def execute_action(
        self,
        host: str,
        port: int,
        username: str,
        password: Optional[str] = None,
        private_key: Optional[str] = None,
        passphrase: Optional[str] = None,
        service_name: str = "",
        action: str = "",  # "start", "stop", "restart", "reload"
    ) -> ServiceActionResult:
        """Execute a service lifecycle action (start/stop/restart/reload)."""
        pass
