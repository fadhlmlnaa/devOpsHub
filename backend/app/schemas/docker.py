import re
import uuid
from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class DockerDaemonState(str, Enum):
    NOT_INSTALLED = "NOT_INSTALLED"
    STOPPED = "STOPPED"
    RUNNING = "RUNNING"
    UNKNOWN = "UNKNOWN"


class ContainerFilterState(str, Enum):
    RUNNING = "running"
    STOPPED = "stopped"
    ALL = "all"


class ComposeProjectStatus(str, Enum):
    RUNNING = "RUNNING"
    STOPPED = "STOPPED"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"
    UNKNOWN = "UNKNOWN"


# --- Validation Helpers ---
CONTAINER_ID_PATTERN = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_.-]{0,127}$")
PROJECT_NAME_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")
COMPOSE_FILE_PATTERN = re.compile(r"^[a-zA-Z0-9_.-]+\.(ya?ml)$")


class DockerStatusResponse(BaseModel):
    server_id: uuid.UUID
    installed: bool
    running: bool
    version: Optional[str] = None
    state: DockerDaemonState
    checked_at: datetime


class DockerContainerSummary(BaseModel):
    id: str
    name: str
    image: str
    status: str
    state: str
    created_at: Optional[str] = None
    ports: List[str] = Field(default_factory=list)


class DockerContainerListResponse(BaseModel):
    server_id: uuid.UUID
    containers: List[DockerContainerSummary]
    checked_at: datetime


class DockerContainerDetail(BaseModel):
    id: str
    name: str
    image: str
    state: str
    status: str
    created_at: Optional[str] = None
    started_at: Optional[str] = None
    ports: List[str] = Field(default_factory=list)
    restart_policy: Optional[str] = None
    cpu_usage: Optional[str] = None
    memory_usage: Optional[str] = None
    checked_at: datetime


class DockerContainerActionRequest(BaseModel):
    confirm: bool = Field(
        ...,
        description="Explicit confirmation flag required for container mutations",
    )


class DockerContainerActionResult(BaseModel):
    success: bool
    container: str
    action: str
    current_state: str
    message: str
    checked_at: datetime


class DockerLogEntry(BaseModel):
    timestamp: Optional[datetime] = None
    message: str


class DockerContainerLogsResponse(BaseModel):
    container: str
    lines_requested: int
    lines_returned: int
    entries: List[DockerLogEntry]
    truncated: bool
    checked_at: datetime


# --- Docker Compose Schemas ---
class DockerComposeProjectCreate(BaseModel):
    environment_id: uuid.UUID
    name: str = Field(..., min_length=2, max_length=255)
    project_name: str = Field(..., min_length=2, max_length=64)
    working_directory: str = Field(..., min_length=1, max_length=512)
    compose_file: str = Field(default="docker-compose.yml", min_length=3, max_length=255)
    description: Optional[str] = None
    is_active: bool = True

    @field_validator("project_name")
    @classmethod
    def validate_project_name(cls, v: str) -> str:
        clean_v = v.strip().lower()
        if not PROJECT_NAME_PATTERN.match(clean_v):
            raise ValueError("project_name hanya boleh huruf kecil, angka, hyphens (-), dan underscore (_).")
        return clean_v

    @field_validator("working_directory")
    @classmethod
    def validate_working_directory(cls, v: str) -> str:
        clean_v = v.strip()
        if not clean_v.startswith("/"):
            raise ValueError("working_directory harus berupa absolute path (diawali '/').")
        if ";" in clean_v or "&" in clean_v or "|" in clean_v or "`" in clean_v or "$" in clean_v:
            raise ValueError("working_directory mengandung karakter tidak diizinkan.")
        return clean_v

    @field_validator("compose_file")
    @classmethod
    def validate_compose_file(cls, v: str) -> str:
        clean_v = v.strip()
        if not COMPOSE_FILE_PATTERN.match(clean_v):
            raise ValueError("compose_file harus berupa nama file yaml/yml valid (contoh: docker-compose.yml).")
        return clean_v


class DockerComposeProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    project_name: Optional[str] = Field(None, min_length=2, max_length=64)
    environment_id: Optional[uuid.UUID] = None
    working_directory: Optional[str] = Field(None, min_length=1, max_length=512)
    compose_file: Optional[str] = Field(None, min_length=3, max_length=255)
    description: Optional[str] = None
    is_active: Optional[bool] = None

    @field_validator("project_name")
    @classmethod
    def validate_project_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            clean_v = v.strip().lower()
            if not PROJECT_NAME_PATTERN.match(clean_v):
                raise ValueError("project_name hanya boleh huruf kecil, angka, hyphens (-), dan underscore (_).")
            return clean_v
        return v

    @field_validator("working_directory")
    @classmethod
    def validate_working_directory(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            clean_v = v.strip()
            if not clean_v.startswith("/"):
                raise ValueError("working_directory harus berupa absolute path (diawali '/').")
            if ";" in clean_v or "&" in clean_v or "|" in clean_v or "`" in clean_v or "$" in clean_v:
                raise ValueError("working_directory mengandung karakter tidak diizinkan.")
            return clean_v
        return v

    @field_validator("compose_file")
    @classmethod
    def validate_compose_file(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            clean_v = v.strip()
            if not COMPOSE_FILE_PATTERN.match(clean_v):
                raise ValueError("compose_file harus berupa nama file yaml/yml valid (contoh: docker-compose.yml).")
            return clean_v
        return v


class DockerComposeProjectResponse(BaseModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    server_id: uuid.UUID
    environment_id: uuid.UUID
    name: str
    project_name: str
    working_directory: str
    compose_file: str
    description: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DockerComposeServiceStatus(BaseModel):
    name: str
    service: Optional[str] = None
    state: str
    status: Optional[str] = None


class DockerComposeStatusResponse(BaseModel):
    project_id: uuid.UUID
    project_name: str
    status: ComposeProjectStatus
    services: List[DockerComposeServiceStatus]
    checked_at: datetime


class DockerComposeActionRequest(BaseModel):
    confirm: bool = Field(
        ...,
        description="Explicit confirmation flag required for compose actions (up/down/restart)",
    )


class DockerComposeActionResult(BaseModel):
    success: bool
    project_id: uuid.UUID
    action: str
    status: ComposeProjectStatus
    message: str
    checked_at: datetime
