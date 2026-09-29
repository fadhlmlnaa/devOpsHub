import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class WorkspaceBase(BaseModel):
    name: str
    description: Optional[str] = None
    timezone: str = "UTC"


class WorkspaceCreate(WorkspaceBase):
    pass


class WorkspaceRead(WorkspaceBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
