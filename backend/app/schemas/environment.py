import re
import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class EnvironmentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Nama Environment (e.g. Production)")
    key: str = Field(..., min_length=1, max_length=100, description="Unique slug key (e.g. production, staging, dev)")
    description: Optional[str] = Field(None, description="Deskripsi environment")

    @field_validator("key")
    @classmethod
    def validate_key(cls, v: str) -> str:
        cleaned = v.strip().lower()
        if not re.match(r"^[a-z0-9_-]+$", cleaned):
            raise ValueError("Key environment hanya boleh berisi huruf kecil, angka, tanda minus (-), dan underscore (_).")
        return cleaned


class EnvironmentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None


class EnvironmentResponse(BaseModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    name: str
    key: str
    description: Optional[str] = None
    server_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
