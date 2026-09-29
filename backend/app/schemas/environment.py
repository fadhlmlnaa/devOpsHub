import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class EnvironmentBase(BaseModel):
    name: str
    key: str
    description: Optional[str] = None


class EnvironmentCreate(EnvironmentBase):
    workspace_id: uuid.UUID


class EnvironmentRead(EnvironmentBase):
    id: uuid.UUID
    workspace_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
