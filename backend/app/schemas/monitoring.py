import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class CPUMetrics(BaseModel):
    usage_percent: Optional[float] = Field(None, ge=0.0, le=100.0, description="CPU utilization percentage (0-100%)")
    cores: Optional[int] = Field(None, ge=1, description="Number of CPU cores")
    error: Optional[str] = None


class MemoryMetrics(BaseModel):
    total_bytes: Optional[int] = Field(None, ge=0, description="Total physical memory in bytes")
    used_bytes: Optional[int] = Field(None, ge=0, description="Used memory in bytes")
    available_bytes: Optional[int] = Field(None, ge=0, description="Available memory in bytes")
    free_bytes: Optional[int] = Field(None, ge=0, description="Free memory in bytes")
    usage_percent: Optional[float] = Field(None, ge=0.0, le=100.0, description="Memory utilization percentage (0-100%)")
    error: Optional[str] = None


class DiskMetrics(BaseModel):
    filesystem: Optional[str] = None
    mount_point: str = "/"
    total_bytes: Optional[int] = Field(None, ge=0, description="Total disk capacity in bytes")
    used_bytes: Optional[int] = Field(None, ge=0, description="Used disk space in bytes")
    available_bytes: Optional[int] = Field(None, ge=0, description="Available disk space in bytes")
    usage_percent: Optional[float] = Field(None, ge=0.0, le=100.0, description="Disk utilization percentage (0-100%)")
    error: Optional[str] = None


class LoadMetrics(BaseModel):
    load_1m: Optional[float] = Field(None, ge=0.0, description="1-minute load average")
    load_5m: Optional[float] = Field(None, ge=0.0, description="5-minute load average")
    load_15m: Optional[float] = Field(None, ge=0.0, description="15-minute load average")
    error: Optional[str] = None


class SystemInfoMetrics(BaseModel):
    hostname: Optional[str] = None
    operating_system: Optional[str] = None
    kernel: Optional[str] = None
    architecture: Optional[str] = None
    error: Optional[str] = None


class NetworkInterface(BaseModel):
    name: str
    addresses: List[str] = []


class NetworkMetrics(BaseModel):
    interfaces: List[NetworkInterface] = []
    error: Optional[str] = None


class ServerMetricsResponse(BaseModel):
    server_id: uuid.UUID
    status: str = Field(..., description="'ONLINE', 'OFFLINE', or 'UNKNOWN'")
    checked_at: datetime = Field(default_factory=datetime.utcnow)
    cpu: Optional[CPUMetrics] = None
    memory: Optional[MemoryMetrics] = None
    disk: Optional[DiskMetrics] = None
    load: Optional[LoadMetrics] = None
    uptime_seconds: Optional[int] = Field(None, ge=0, description="Server uptime in seconds")
    system: Optional[SystemInfoMetrics] = None
    network: Optional[NetworkMetrics] = None
    message: Optional[str] = None
    error: Optional[str] = None
