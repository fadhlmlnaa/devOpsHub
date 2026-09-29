import uuid
from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class SinceFilter(str, Enum):
    FIVE_MINUTES = "5m"
    TEN_MINUTES = "10m"
    THIRTY_MINUTES = "30m"
    ONE_HOUR = "1h"
    SIX_HOURS = "6h"
    TWELVE_HOURS = "12h"
    TWENTY_FOUR_HOURS = "24h"


class LogPriority(str, Enum):
    EMERGENCY = "EMERGENCY"
    ALERT = "ALERT"
    CRITICAL = "CRITICAL"
    ERROR = "ERROR"
    WARNING = "WARNING"
    NOTICE = "NOTICE"
    INFO = "INFO"
    DEBUG = "DEBUG"
    UNKNOWN = "UNKNOWN"


class LogEntry(BaseModel):
    timestamp: Optional[datetime] = Field(None, description="Waktu log dibuat (ISO UTC)")
    priority: str = Field("INFO", description="Tingkat prioritas log (INFO, ERROR, WARNING, etc.)")
    message: str = Field(..., description="Isi teks pesan log")

    model_config = ConfigDict(from_attributes=True)


class LogResponse(BaseModel):
    server_id: uuid.UUID
    service: str
    lines_requested: int
    lines_returned: int
    since: Optional[str] = None
    truncated: bool = False
    entries: List[LogEntry] = Field(default_factory=list)
    checked_at: datetime

    model_config = ConfigDict(from_attributes=True)
