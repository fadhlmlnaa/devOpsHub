import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class AuditAction(str, Enum):
    # Auth
    AUTH_LOGIN = "AUTH_LOGIN"
    AUTH_LOGOUT = "AUTH_LOGOUT"
    AUTH_REFRESH = "AUTH_REFRESH"
    AUTH_REGISTER = "AUTH_REGISTER"

    # Workspace
    WORKSPACE_CREATED = "WORKSPACE_CREATED"
    WORKSPACE_UPDATED = "WORKSPACE_UPDATED"
    WORKSPACE_MEMBER_ADDED = "WORKSPACE_MEMBER_ADDED"
    WORKSPACE_MEMBER_REMOVED = "WORKSPACE_MEMBER_REMOVED"
    WORKSPACE_ROLE_CHANGED = "WORKSPACE_ROLE_CHANGED"

    # Server
    SERVER_CREATED = "SERVER_CREATED"
    SERVER_UPDATED = "SERVER_UPDATED"
    SERVER_DELETED = "SERVER_DELETED"
    SERVER_CONNECTION_TESTED = "SERVER_CONNECTION_TESTED"

    # Services
    SERVICE_STARTED = "SERVICE_STARTED"
    SERVICE_STOPPED = "SERVICE_STOPPED"
    SERVICE_RESTARTED = "SERVICE_RESTARTED"
    SERVICE_RELOADED = "SERVICE_RELOADED"

    # Docker
    DOCKER_CONTAINER_STARTED = "DOCKER_CONTAINER_STARTED"
    DOCKER_CONTAINER_STOPPED = "DOCKER_CONTAINER_STOPPED"
    DOCKER_CONTAINER_RESTARTED = "DOCKER_CONTAINER_RESTARTED"
    DOCKER_COMPOSE_STARTED = "DOCKER_COMPOSE_STARTED"
    DOCKER_COMPOSE_STOPPED = "DOCKER_COMPOSE_STOPPED"
    DOCKER_COMPOSE_RESTARTED = "DOCKER_COMPOSE_RESTARTED"

    # Deployments
    DEPLOYMENT_STARTED = "DEPLOYMENT_STARTED"
    DEPLOYMENT_SUCCEEDED = "DEPLOYMENT_SUCCEEDED"
    DEPLOYMENT_FAILED = "DEPLOYMENT_FAILED"

    # Backups
    BACKUP_STARTED = "BACKUP_STARTED"
    BACKUP_SUCCEEDED = "BACKUP_SUCCEEDED"
    BACKUP_FAILED = "BACKUP_FAILED"
    BACKUP_VERIFIED = "BACKUP_VERIFIED"

    # Alerts & Notifications
    ALERT_RULE_CREATED = "ALERT_RULE_CREATED"
    ALERT_RULE_UPDATED = "ALERT_RULE_UPDATED"
    ALERT_RULE_DELETED = "ALERT_RULE_DELETED"
    NOTIFICATION_READ = "NOTIFICATION_READ"


class AuditStatus(str, Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    DENIED = "DENIED"


class AuditUserSummary(BaseModel):
    id: uuid.UUID
    name: str
    email: str

    model_config = ConfigDict(from_attributes=True)


class AuditLogResponse(BaseModel):
    id: uuid.UUID
    workspace_id: Optional[uuid.UUID] = None
    user_id: Optional[uuid.UUID] = None
    user: Optional[AuditUserSummary] = None
    action: str
    resource_type: str
    resource_id: Optional[str] = None
    environment_id: Optional[uuid.UUID] = None
    server_id: Optional[uuid.UUID] = None
    status: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = Field(default=None, alias="meta_data")
    created_at: datetime

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class AuditLogListResponse(BaseModel):
    items: List[AuditLogResponse]
    total: int
    limit: int
    offset: int
