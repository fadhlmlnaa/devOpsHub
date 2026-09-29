import re
import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator

SERVICE_NAME_PATTERN = re.compile(r"^[A-Za-z0-9_.@:-]+\.service$")


def validate_service_name_format(value: str) -> str:
    cleaned = value.strip()
    if not SERVICE_NAME_PATTERN.match(cleaned):
        raise ValueError(
            "Format nama service tidak valid. Harus berakhiran '.service' dan hanya memuat karakter alfanumerik, '.', '_', '-', '@', atau ':' tanpa spasi atau karakter shell."
        )
    return cleaned


class ServiceSummary(BaseModel):
    name: str
    load_state: str = Field(..., description="Status pemuatan unit (e.g. loaded, not-found)")
    active_state: str = Field(..., description="Status keaktifan (e.g. active, inactive, failed)")
    sub_state: str = Field(..., description="Sub-status (e.g. running, dead, exited)")
    description: Optional[str] = None
    enabled: Optional[bool] = None

    model_config = ConfigDict(from_attributes=True)


class ServiceListResponse(BaseModel):
    server_id: uuid.UUID
    systemd_supported: bool
    services: List[ServiceSummary] = Field(default_factory=list)
    checked_at: datetime
    message: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ServiceDetailResponse(BaseModel):
    server_id: uuid.UUID
    name: str
    load_state: str
    active_state: str
    sub_state: str
    enabled: Optional[bool] = None
    description: Optional[str] = None
    main_pid: Optional[int] = None
    active_enter_timestamp: Optional[str] = None
    checked_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ServiceActionRequest(BaseModel):
    confirm: bool = Field(..., description="Konfirmasi eksplisit bahwa operasi service disetujui")

    @field_validator("confirm")
    @classmethod
    def require_true_confirmation(cls, v: bool) -> bool:
        if not v:
            raise ValueError("Operasi service membutuhkan konfirmasi eksplisit (confirm=true).")
        return v


class ServiceStateSummary(BaseModel):
    active_state: str
    sub_state: str

    model_config = ConfigDict(from_attributes=True)


class ServiceActionResponse(BaseModel):
    success: bool
    service: str
    action: str
    previous_state: Optional[ServiceStateSummary] = None
    current_state: Optional[ServiceStateSummary] = None
    message: str
    checked_at: datetime

    model_config = ConfigDict(from_attributes=True)
