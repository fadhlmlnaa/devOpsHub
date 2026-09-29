from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class DockerStatusResult:
    installed: bool
    running: bool
    version: Optional[str] = None
    state: str = "UNKNOWN"
    error: Optional[str] = None


@dataclass
class ContainerSummaryResult:
    id: str
    name: str
    image: str
    status: str
    state: str
    created_at: Optional[str] = None
    ports: List[str] = field(default_factory=list)


@dataclass
class ContainerDetailResult:
    id: str
    name: str
    image: str
    state: str
    status: str
    created_at: Optional[str] = None
    started_at: Optional[str] = None
    ports: List[str] = field(default_factory=list)
    restart_policy: Optional[str] = None
    cpu_usage: Optional[str] = None
    memory_usage: Optional[str] = None


@dataclass
class ContainerActionResult:
    success: bool
    container: str
    action: str
    current_state: str
    message: str
    error: Optional[str] = None


@dataclass
class ContainerLogEntryResult:
    timestamp: Optional[datetime]
    message: str


@dataclass
class ContainerLogsResult:
    container: str
    lines_requested: int
    lines_returned: int
    truncated: bool = False
    entries: List[ContainerLogEntryResult] = field(default_factory=list)
    error: Optional[str] = None


@dataclass
class ComposeServiceStatusResult:
    name: str
    service: Optional[str] = None
    state: str = "unknown"
    status: Optional[str] = None


@dataclass
class ComposeStatusResult:
    project_name: str
    status: str  # RUNNING, STOPPED, PARTIAL, FAILED, UNKNOWN
    services: List[ComposeServiceStatusResult] = field(default_factory=list)
    error: Optional[str] = None


@dataclass
class ComposeActionResult:
    success: bool
    project_name: str
    action: str
    status: str
    message: str
    error: Optional[str] = None


class DockerProvider(ABC):
    """Abstract base class for Docker providers (SSH, Agent, etc.)."""

    @abstractmethod
    async def get_docker_status(
        self,
        host: str,
        port: int,
        username: str,
        password: Optional[str] = None,
        private_key: Optional[str] = None,
        passphrase: Optional[str] = None,
    ) -> DockerStatusResult:
        pass

    @abstractmethod
    async def list_containers(
        self,
        host: str,
        port: int,
        username: str,
        password: Optional[str] = None,
        private_key: Optional[str] = None,
        passphrase: Optional[str] = None,
        state_filter: str = "running",
    ) -> List[ContainerSummaryResult]:
        pass

    @abstractmethod
    async def get_container_detail(
        self,
        host: str,
        port: int,
        username: str,
        password: Optional[str] = None,
        private_key: Optional[str] = None,
        passphrase: Optional[str] = None,
        container_id: str = "",
    ) -> Optional[ContainerDetailResult]:
        pass

    @abstractmethod
    async def execute_container_action(
        self,
        host: str,
        port: int,
        username: str,
        password: Optional[str] = None,
        private_key: Optional[str] = None,
        passphrase: Optional[str] = None,
        container_id: str = "",
        action: str = "restart",
    ) -> ContainerActionResult:
        pass

    @abstractmethod
    async def get_container_logs(
        self,
        host: str,
        port: int,
        username: str,
        password: Optional[str] = None,
        private_key: Optional[str] = None,
        passphrase: Optional[str] = None,
        container_id: str = "",
        lines: int = 100,
        since: Optional[str] = None,
    ) -> ContainerLogsResult:
        pass

    @abstractmethod
    async def get_compose_status(
        self,
        host: str,
        port: int,
        username: str,
        password: Optional[str] = None,
        private_key: Optional[str] = None,
        passphrase: Optional[str] = None,
        working_directory: str = "",
        compose_file: str = "docker-compose.yml",
        project_name: str = "",
    ) -> ComposeStatusResult:
        pass

    @abstractmethod
    async def execute_compose_action(
        self,
        host: str,
        port: int,
        username: str,
        password: Optional[str] = None,
        private_key: Optional[str] = None,
        passphrase: Optional[str] = None,
        working_directory: str = "",
        compose_file: str = "docker-compose.yml",
        project_name: str = "",
        action: str = "restart",
    ) -> ComposeActionResult:
        pass
