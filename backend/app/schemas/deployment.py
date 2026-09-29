from datetime import datetime
from enum import Enum
import re
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field, field_validator


class DeploymentTypeEnum(str, Enum):
    SYSTEMD = "SYSTEMD"
    DOCKER_COMPOSE = "DOCKER_COMPOSE"


class DeploymentStatusEnum(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class DeploymentOperationEnum(str, Enum):
    GIT_PULL = "GIT_PULL"
    INSTALL_DEPENDENCIES = "INSTALL_DEPENDENCIES"
    BUILD = "BUILD"
    DOCKER_COMPOSE_PULL = "DOCKER_COMPOSE_PULL"
    DOCKER_COMPOSE_UP = "DOCKER_COMPOSE_UP"
    RESTART_SERVICE = "RESTART_SERVICE"
    HEALTH_CHECK = "HEALTH_CHECK"


class HealthCheckTypeEnum(str, Enum):
    NONE = "NONE"
    SERVICE_STATUS = "SERVICE_STATUS"
    DOCKER_COMPOSE_STATUS = "DOCKER_COMPOSE_STATUS"
    HTTP_HEALTH_CHECK = "HTTP_HEALTH_CHECK"


class LogLevelEnum(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


# Validation regex patterns
WORKING_DIR_PATTERN = re.compile(r"^/[a-zA-Z0-9_./-]*$")
BRANCH_PATTERN = re.compile(r"^[a-zA-Z0-9._/-]{1,255}$")
SERVICE_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9_.@:-]+\.service$")
COMPOSE_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_.-]{0,63}$")


class DeploymentStepItem(BaseModel):
    operation: DeploymentOperationEnum
    options: Optional[Dict[str, Any]] = None


class DeploymentConfigBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    application_name: str = Field(..., min_length=1, max_length=255)
    working_directory: str = Field(..., min_length=1, max_length=1024)
    deployment_type: DeploymentTypeEnum = DeploymentTypeEnum.SYSTEMD
    branch: Optional[str] = Field(None, max_length=255)
    repository_url: Optional[str] = Field(None, max_length=1024)
    pre_deploy_steps: Optional[List[DeploymentStepItem]] = Field(default_factory=list)
    deploy_steps: Optional[List[DeploymentStepItem]] = Field(default_factory=list)
    post_deploy_steps: Optional[List[DeploymentStepItem]] = Field(default_factory=list)
    restart_service_name: Optional[str] = Field(None, max_length=255)
    compose_project_name: Optional[str] = Field(None, max_length=255)
    health_check_type: Optional[HealthCheckTypeEnum] = HealthCheckTypeEnum.NONE
    health_check_url: Optional[str] = Field(None, max_length=1024)
    is_active: bool = True

    @field_validator("working_directory")
    @classmethod
    def validate_working_directory(cls, v: str) -> str:
        v = v.strip()
        if not v.startswith("/"):
            raise ValueError("Working directory must be an absolute path starting with '/'.")
        if ".." in v or ";" in v or "&&" in v or "|" in v or "$" in v or "`" in v:
            raise ValueError("Working directory contains invalid or unsafe characters.")
        if not WORKING_DIR_PATTERN.match(v):
            raise ValueError("Working directory contains forbidden characters.")
        return v

    @field_validator("branch")
    @classmethod
    def validate_branch(cls, v: Optional[str]) -> Optional[str]:
        if v is None or not v.strip():
            return None
        v = v.strip()
        if not BRANCH_PATTERN.match(v) or ".." in v or ";" in v or "&" in v or "|" in v:
            raise ValueError("Branch name contains invalid or unsafe characters.")
        return v

    @field_validator("restart_service_name")
    @classmethod
    def validate_restart_service_name(cls, v: Optional[str]) -> Optional[str]:
        if v is None or not v.strip():
            return None
        v = v.strip()
        if not SERVICE_NAME_PATTERN.match(v):
            raise ValueError("Service name must be a valid systemd unit ending with '.service'.")
        return v

    @field_validator("compose_project_name")
    @classmethod
    def validate_compose_project_name(cls, v: Optional[str]) -> Optional[str]:
        if v is None or not v.strip():
            return None
        v = v.strip()
        if not COMPOSE_NAME_PATTERN.match(v):
            raise ValueError("Compose project name contains invalid characters.")
        return v

    @field_validator("health_check_url")
    @classmethod
    def validate_health_check_url(cls, v: Optional[str]) -> Optional[str]:
        if v is None or not v.strip():
            return None
        v = v.strip()
        if not (v.startswith("http://") or v.startswith("https://")):
            raise ValueError("Health check URL must start with 'http://' or 'https://'.")
        if any(c in v for c in [";", "&", "|", "$", "`", "\n", "\r", " "]):
            raise ValueError("Health check URL contains unsafe characters.")
        return v


class DeploymentConfigCreate(DeploymentConfigBase):
    environment_id: uuid.UUID
    server_id: uuid.UUID


class DeploymentConfigUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    application_name: Optional[str] = Field(None, min_length=1, max_length=255)
    working_directory: Optional[str] = Field(None, min_length=1, max_length=1024)
    deployment_type: Optional[DeploymentTypeEnum] = None
    branch: Optional[str] = Field(None, max_length=255)
    repository_url: Optional[str] = Field(None, max_length=1024)
    pre_deploy_steps: Optional[List[DeploymentStepItem]] = None
    deploy_steps: Optional[List[DeploymentStepItem]] = None
    post_deploy_steps: Optional[List[DeploymentStepItem]] = None
    restart_service_name: Optional[str] = Field(None, max_length=255)
    compose_project_name: Optional[str] = Field(None, max_length=255)
    health_check_type: Optional[HealthCheckTypeEnum] = None
    health_check_url: Optional[str] = Field(None, max_length=1024)
    is_active: Optional[bool] = None

    @field_validator("working_directory")
    @classmethod
    def validate_working_directory(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        v = v.strip()
        if not v.startswith("/"):
            raise ValueError("Working directory must be an absolute path starting with '/'.")
        if ".." in v or ";" in v or "&&" in v or "|" in v or "$" in v or "`" in v:
            raise ValueError("Working directory contains invalid or unsafe characters.")
        if not WORKING_DIR_PATTERN.match(v):
            raise ValueError("Working directory contains forbidden characters.")
        return v

    @field_validator("branch")
    @classmethod
    def validate_branch(cls, v: Optional[str]) -> Optional[str]:
        if v is None or not v.strip():
            return None
        v = v.strip()
        if not BRANCH_PATTERN.match(v) or ".." in v or ";" in v or "&" in v or "|" in v:
            raise ValueError("Branch name contains invalid or unsafe characters.")
        return v

    @field_validator("restart_service_name")
    @classmethod
    def validate_restart_service_name(cls, v: Optional[str]) -> Optional[str]:
        if v is None or not v.strip():
            return None
        v = v.strip()
        if not SERVICE_NAME_PATTERN.match(v):
            raise ValueError("Service name must be a valid systemd unit ending with '.service'.")
        return v

    @field_validator("compose_project_name")
    @classmethod
    def validate_compose_project_name(cls, v: Optional[str]) -> Optional[str]:
        if v is None or not v.strip():
            return None
        v = v.strip()
        if not COMPOSE_NAME_PATTERN.match(v):
            raise ValueError("Compose project name contains invalid characters.")
        return v

    @field_validator("health_check_url")
    @classmethod
    def validate_health_check_url(cls, v: Optional[str]) -> Optional[str]:
        if v is None or not v.strip():
            return None
        v = v.strip()
        if not (v.startswith("http://") or v.startswith("https://")):
            raise ValueError("Health check URL must start with 'http://' or 'https://'.")
        if any(c in v for c in [";", "&", "|", "$", "`", "\n", "\r", " "]):
            raise ValueError("Health check URL contains unsafe characters.")
        return v


class DeploymentConfigResponse(DeploymentConfigBase):
    id: uuid.UUID
    workspace_id: uuid.UUID
    environment_id: uuid.UUID
    server_id: uuid.UUID
    environment_name: Optional[str] = None
    environment_is_protected: Optional[bool] = False
    server_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DeploymentTriggerRequest(BaseModel):
    confirm: bool = Field(..., description="Explicit confirmation required to trigger deployment.")


class DeploymentResponse(BaseModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    environment_id: uuid.UUID
    server_id: uuid.UUID
    deployment_config_id: uuid.UUID
    status: str
    triggered_by_user_id: Optional[uuid.UUID] = None
    triggered_by_name: Optional[str] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    commit_reference: Optional[str] = None
    message: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    deployment_config_name: Optional[str] = None
    environment_name: Optional[str] = None
    environment_is_protected: Optional[bool] = False
    server_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class DeploymentListResponse(BaseModel):
    items: List[DeploymentResponse]
    total: int
    page: int
    limit: int


class DeploymentLogEntry(BaseModel):
    sequence: int
    timestamp: datetime
    level: str
    message: str

    model_config = ConfigDict(from_attributes=True)


class DeploymentLogsResponse(BaseModel):
    deployment_id: uuid.UUID
    status: str
    lines_returned: int
    entries: List[DeploymentLogEntry]
    checked_at: datetime = Field(default_factory=lambda: datetime.now())
