from datetime import datetime
from enum import Enum
import re
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field, field_validator


class BackupTypeEnum(str, Enum):
    POSTGRESQL = "POSTGRESQL"
    FILESYSTEM = "FILESYSTEM"
    DOCKER_VOLUME = "DOCKER_VOLUME"


class BackupStatusEnum(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class BackupLogLevelEnum(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


# Validation regex patterns
PATH_PATTERN = re.compile(r"^/[a-zA-Z0-9_./-]*$")
DB_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9_.-]{1,63}$")
VOLUME_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_.-]{0,127}$")


class BackupConfigBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    backup_type: BackupTypeEnum = BackupTypeEnum.POSTGRESQL
    source: str = Field(..., min_length=1, max_length=1024)
    destination: str = Field(..., min_length=1, max_length=1024)
    retention_days: int = Field(7, ge=1, le=365)
    is_compressed: bool = True
    is_active: bool = True

    @field_validator("destination")
    @classmethod
    def validate_destination(cls, v: str) -> str:
        clean = v.strip()
        if not clean.startswith("/"):
            raise ValueError("Destination harus berupa absolute path (diawali '/').")
        if ".." in clean:
            raise ValueError("Path traversal ('..') dilarang pada destination path.")
        if not PATH_PATTERN.match(clean):
            raise ValueError("Destination mengandung karakter tidak valid.")
        return clean

    @field_validator("source")
    @classmethod
    def validate_source(cls, v: str, info) -> str:
        clean = v.strip()
        backup_type = info.data.get("backup_type")

        if backup_type == BackupTypeEnum.FILESYSTEM:
            if not clean.startswith("/"):
                raise ValueError("Source filesystem harus berupa absolute path (diawali '/').")
            if ".." in clean:
                raise ValueError("Path traversal ('..') dilarang pada source path.")
            if not PATH_PATTERN.match(clean):
                raise ValueError("Source path mengandung karakter tidak valid.")
        elif backup_type == BackupTypeEnum.POSTGRESQL:
            if not DB_NAME_PATTERN.match(clean):
                raise ValueError("Nama database PostgreSQL tidak valid.")
        elif backup_type == BackupTypeEnum.DOCKER_VOLUME:
            if not VOLUME_NAME_PATTERN.match(clean):
                raise ValueError("Nama docker volume tidak valid.")

        return clean


class BackupConfigCreate(BackupConfigBase):
    environment_id: uuid.UUID
    server_id: uuid.UUID


class BackupConfigUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    source: Optional[str] = Field(None, min_length=1, max_length=1024)
    destination: Optional[str] = Field(None, min_length=1, max_length=1024)
    retention_days: Optional[int] = Field(None, ge=1, le=365)
    is_compressed: Optional[bool] = None
    is_active: Optional[bool] = None

    @field_validator("destination")
    @classmethod
    def validate_destination(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        clean = v.strip()
        if not clean.startswith("/"):
            raise ValueError("Destination harus berupa absolute path (diawali '/').")
        if ".." in clean:
            raise ValueError("Path traversal ('..') dilarang pada destination path.")
        if not PATH_PATTERN.match(clean):
            raise ValueError("Destination mengandung karakter tidak valid.")
        return clean


class BackupConfigResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    workspace_id: uuid.UUID
    environment_id: uuid.UUID
    server_id: uuid.UUID
    name: str
    description: Optional[str]
    backup_type: str
    source: str
    destination: str
    retention_days: int
    is_compressed: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime

    # Augmented fields
    environment_name: Optional[str] = None
    environment_is_protected: Optional[bool] = False
    server_name: Optional[str] = None


class BackupTriggerRequest(BaseModel):
    confirm: bool = Field(..., description="Wajib true untuk mengeksekusi backup")


class BackupVerifyRequest(BaseModel):
    confirm: bool = Field(True, description="Konfirmasi verifikasi backup")


class BackupVerifyResponse(BaseModel):
    backup_id: uuid.UUID
    verified: bool
    stored_checksum: Optional[str] = None
    calculated_checksum: Optional[str] = None
    file_exists: bool
    verified_at: datetime
    message: str


class BackupResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    workspace_id: uuid.UUID
    environment_id: uuid.UUID
    server_id: uuid.UUID
    backup_config_id: uuid.UUID
    status: str
    started_at: datetime
    finished_at: Optional[datetime] = None
    file_name: Optional[str] = None
    file_path: Optional[str] = None
    file_size_bytes: Optional[int] = None
    checksum: Optional[str] = None
    error_message: Optional[str] = None
    triggered_by_user_id: Optional[uuid.UUID] = None
    created_at: datetime

    # Augmented fields
    backup_config_name: Optional[str] = None
    backup_type: Optional[str] = None
    environment_name: Optional[str] = None
    environment_is_protected: Optional[bool] = False
    server_name: Optional[str] = None
    triggered_by_name: Optional[str] = None


class BackupListResponse(BaseModel):
    total: int
    page: int
    limit: int
    items: List[BackupResponse]


class BackupLogEntry(BaseModel):
    sequence: int
    timestamp: datetime
    level: str
    message: str


class BackupLogsResponse(BaseModel):
    backup_id: uuid.UUID
    status: str
    lines_returned: int
    entries: List[BackupLogEntry]
