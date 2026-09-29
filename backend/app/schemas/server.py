import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class ServerBase(BaseModel):
    name: str
    hostname: Optional[str] = None
    ip_address: Optional[str] = None
    ssh_port: int = Field(default=22, ge=1, le=65535)
    username: Optional[str] = None
    operating_system: Optional[str] = None
    description: Optional[str] = None
    is_active: bool = True


class ServerCreate(ServerBase):
    workspace_id: uuid.UUID
    environment_id: uuid.UUID


class ServerRead(ServerBase):
    id: uuid.UUID
    workspace_id: uuid.UUID
    environment_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
