import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator


class ServerCredentialInput(BaseModel):
    auth_type: str = Field("PASSWORD", description="'PASSWORD' or 'PRIVATE_KEY'")
    username: str = Field(..., min_length=1, max_length=64, description="SSH Username (e.g. root, ubuntu)")
    password: Optional[str] = Field(None, description="SSH Password (encrypted at rest)")
    private_key: Optional[str] = Field(None, description="SSH Private Key in PEM/OpenSSH format")
    passphrase: Optional[str] = Field(None, description="Passphrase for encrypted private key")

    @field_validator("auth_type")
    @classmethod
    def validate_auth_type(cls, v: str) -> str:
        upper = v.strip().upper()
        if upper not in ("PASSWORD", "PRIVATE_KEY"):
            raise ValueError("auth_type harus bernilai 'PASSWORD' atau 'PRIVATE_KEY'.")
        return upper


class EnvironmentSummary(BaseModel):
    id: uuid.UUID
    name: str
    key: str

    model_config = {"from_attributes": True}


class ServerCreate(BaseModel):
    environment_id: uuid.UUID = Field(..., description="ID Environment dalam workspace")
    name: str = Field(..., min_length=1, max_length=255, description="Nama server")
    hostname: Optional[str] = Field(None, max_length=255, description="Hostname atau FQDN")
    ip_address: Optional[str] = Field(None, max_length=64, description="IP Address publik/privat")
    ssh_port: int = Field(22, ge=1, le=65535, description="Port SSH")
    username: Optional[str] = Field(None, max_length=64, description="Default SSH Username")
    operating_system: Optional[str] = Field(None, max_length=64, description="Operating System (e.g. Ubuntu 24.04)")
    description: Optional[str] = None
    is_active: bool = Field(True, description="Status aktif server")
    credential: Optional[ServerCredentialInput] = None


class ServerUpdate(BaseModel):
    environment_id: Optional[uuid.UUID] = None
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    hostname: Optional[str] = None
    ip_address: Optional[str] = None
    ssh_port: Optional[int] = Field(None, ge=1, le=65535)
    username: Optional[str] = None
    operating_system: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    credential: Optional[ServerCredentialInput] = None


class ServerResponse(BaseModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    environment_id: uuid.UUID
    name: str
    hostname: Optional[str] = None
    ip_address: Optional[str] = None
    ssh_port: int = 22
    username: Optional[str] = None
    operating_system: Optional[str] = None
    description: Optional[str] = None
    is_active: bool = True
    environment: Optional[EnvironmentSummary] = None
    has_credential: bool = False
    auth_type: Optional[str] = None
    status: str = "UNKNOWN"
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ConnectionTestResponse(BaseModel):
    success: bool
    message: str
    status: str  # "ONLINE" or "OFFLINE"
    server_info: Optional[Dict[str, Any]] = None
