import uuid
from datetime import datetime
from pydantic import BaseModel, EmailStr, ConfigDict, Field, field_validator
from app.models.workspace_member import WorkspaceRole


class WorkspaceMemberCreate(BaseModel):
    email: EmailStr = Field(..., description="Email pengguna yang akan ditambahkan")
    role: WorkspaceRole = Field(
        default=WorkspaceRole.DEVELOPER,
        description="Role pengguna dalam workspace (ADMIN, DEVELOPER, VIEWER)",
    )

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.strip().lower()


class WorkspaceMemberRoleUpdate(BaseModel):
    role: WorkspaceRole = Field(
        ...,
        description="Role baru untuk member (ADMIN, DEVELOPER, VIEWER)",
    )


class WorkspaceMemberResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    email: EmailStr
    role: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
