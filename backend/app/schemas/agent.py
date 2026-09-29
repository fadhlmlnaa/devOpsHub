import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, ConfigDict, Field


class AgentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    server_id: uuid.UUID
    workspace_id: uuid.UUID
    name: str
    agent_version: str
    status: str
    last_seen_at: Optional[datetime] = None
    connected_at: Optional[datetime] = None
    disconnected_at: Optional[datetime] = None
    hostname: Optional[str] = None
    operating_system: Optional[str] = None
    architecture: Optional[str] = None
    capabilities: Dict[str, Any] = Field(default_factory=dict)
    is_active: bool
    created_at: datetime
    updated_at: datetime


class AgentEnrollmentRequest(BaseModel):
    expires_in_minutes: int = Field(default=15, ge=1, le=1440)


class AgentEnrollmentResponse(BaseModel):
    enrollment_token: str
    server_id: uuid.UUID
    workspace_id: uuid.UUID
    expires_at: datetime
    installer_command: str


class AgentRegisterRequest(BaseModel):
    enrollment_token: str
    hostname: Optional[str] = None
    operating_system: Optional[str] = None
    architecture: Optional[str] = None
    agent_version: str = "1.0.0"
    capabilities: Dict[str, Any] = Field(default_factory=dict)


class AgentRegisterResponse(BaseModel):
    agent_id: uuid.UUID
    server_id: uuid.UUID
    workspace_id: uuid.UUID
    agent_token: str


class AgentHeartbeatRequest(BaseModel):
    agent_id: uuid.UUID
    agent_version: str = "1.0.0"
    hostname: Optional[str] = None
    operating_system: Optional[str] = None
    architecture: Optional[str] = None
    capabilities: Dict[str, Any] = Field(default_factory=dict)
    status: str = "ONLINE"


class AgentHeartbeatResponse(BaseModel):
    acknowledged: bool = True
    server_time: datetime


class AgentJobPayload(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    job_id: uuid.UUID
    agent_id: uuid.UUID
    server_id: uuid.UUID
    workspace_id: uuid.UUID
    operation: str
    payload: Optional[Dict[str, Any]] = None
    nonce: str
    timeout_seconds: int = 30
    created_at: datetime
    expires_at: datetime


class AgentJobResultRequest(BaseModel):
    job_id: uuid.UUID
    nonce: str
    status: str  # SUCCESS, FAILED
    result: Optional[Dict[str, Any]] = None
    error_category: Optional[str] = None
    error_message: Optional[str] = None


class AgentJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    agent_id: uuid.UUID
    workspace_id: uuid.UUID
    server_id: uuid.UUID
    operation: str
    status: str
    request_id: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None
    result: Optional[Dict[str, Any]] = None
    error_category: Optional[str] = None
    error_message: Optional[str] = None
    timeout_seconds: int
    created_at: datetime
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    expires_at: datetime
