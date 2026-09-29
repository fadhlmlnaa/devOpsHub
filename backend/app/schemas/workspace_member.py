import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.models.workspace_member import WorkspaceRole


class WorkspaceMemberBase(BaseModel):
    workspace_id: uuid.UUID
    user_id: uuid.UUID
    role: WorkspaceRole = WorkspaceRole.VIEWER


class WorkspaceMemberCreate(WorkspaceMemberBase):
    pass


class WorkspaceMemberRead(WorkspaceMemberBase):
    id: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
