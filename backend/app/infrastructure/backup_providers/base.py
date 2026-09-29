from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional


@dataclass
class BackupExecutionResult:
    success: bool
    status: str  # "SUCCESS", "FAILED"
    file_name: Optional[str] = None
    file_path: Optional[str] = None
    file_size_bytes: Optional[int] = None
    checksum: Optional[str] = None
    error_message: Optional[str] = None
    logs: Optional[List[Dict[str, Any]]] = None


@dataclass
class BackupVerificationResult:
    verified: bool
    file_exists: bool
    stored_checksum: Optional[str] = None
    calculated_checksum: Optional[str] = None
    message: str = ""


class BackupProvider(ABC):
    """Abstract interface for executing and verifying backups."""

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
        """Validates that destination directory and source exist and are accessible."""
        pass

    @abstractmethod
    async def execute(
        self,
        host: str,
        port: int,
        username: str,
        password: Optional[str] = None,
        private_key: Optional[str] = None,
        passphrase: Optional[str] = None,
        config: Any = None,
        log_callback: Optional[Callable[[str, str, int, datetime], Any]] = None,
    ) -> BackupExecutionResult:
        """Executes a controlled predefined backup operation."""
        pass

    @abstractmethod
    async def verify(
        self,
        host: str,
        port: int,
        username: str,
        password: Optional[str] = None,
        private_key: Optional[str] = None,
        passphrase: Optional[str] = None,
        file_path: str = "",
        expected_checksum: Optional[str] = None,
    ) -> BackupVerificationResult:
        """Verifies backup integrity by calculating SHA-256 and checking file presence."""
        pass
