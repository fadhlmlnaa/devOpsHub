import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class WorkspaceBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Nama workspace")
    description: Optional[str] = Field(None, max_length=1000, description="Deskripsi workspace")
    timezone: str = Field("UTC", max_length=64, description="Timezone canonical workspace")


class WorkspaceCreate(WorkspaceBase):
    pass


class WorkspaceUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Nama baru workspace")
    description: Optional[str] = Field(None, max_length=1000, description="Deskripsi baru workspace")
    timezone: Optional[str] = Field(None, max_length=64, description="Timezone baru workspace")


class WorkspaceListItem(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str] = None
    timezone: str
    role: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WorkspaceDetailResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str] = None
    timezone: str
    role: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
