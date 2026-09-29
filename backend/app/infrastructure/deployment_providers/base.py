from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional


@dataclass
class DeploymentExecutionResult:
    success: bool
    status: str  # "SUCCESS", "FAILED", "CANCELLED"
    commit_reference: Optional[str] = None
    message: str = ""
    error_message: Optional[str] = None
    logs: List[Dict[str, Any]] = field(default_factory=list)


class DeploymentProvider(ABC):
    """Abstract interface for Deployment execution providers."""

    @abstractmethod
    async def deploy(
        self,
        host: str,
        port: int,
        username: str,
        password: Optional[str] = None,
        private_key: Optional[str] = None,
        passphrase: Optional[str] = None,
        config: Any = None,
        log_callback: Optional[Callable[[str, str], Any]] = None,
    ) -> DeploymentExecutionResult:
        """Executes a deployment according to the given configuration."""
        pass

    @abstractmethod
    async def validate_environment(
        self,
        host: str,
        port: int,
        username: str,
        password: Optional[str] = None,
        private_key: Optional[str] = None,
        passphrase: Optional[str] = None,
        config: Any = None,
    ) -> tuple[bool, str]:
        """Validates if the target server and working directory are accessible."""
        pass
