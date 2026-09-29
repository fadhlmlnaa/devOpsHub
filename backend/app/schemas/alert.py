import re
from datetime import datetime
from enum import Enum
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict


class MetricType(str, Enum):
    CPU_USAGE = "CPU_USAGE"
    MEMORY_USAGE = "MEMORY_USAGE"
    DISK_USAGE = "DISK_USAGE"
    LOAD_AVERAGE = "LOAD_AVERAGE"
    SERVER_STATUS = "SERVER_STATUS"
    SERVICE_STATUS = "SERVICE_STATUS"
    DEPLOYMENT_STATUS = "DEPLOYMENT_STATUS"
    BACKUP_STATUS = "BACKUP_STATUS"


class AlertOperator(str, Enum):
    GREATER_THAN = "GREATER_THAN"
    GREATER_THAN_OR_EQUAL = "GREATER_THAN_OR_EQUAL"
    LESS_THAN = "LESS_THAN"
    LESS_THAN_OR_EQUAL = "LESS_THAN_OR_EQUAL"
    EQUAL = "EQUAL"
    NOT_EQUAL = "NOT_EQUAL"


class AlertSeverity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class AlertStatus(str, Enum):
    FIRING = "FIRING"
    RESOLVED = "RESOLVED"


class AlertEventType(str, Enum):
    TRIGGERED = "TRIGGERED"
    NOTIFICATION_SENT = "NOTIFICATION_SENT"
    RESOLVED = "RESOLVED"
    NOTIFICATION_FAILED = "NOTIFICATION_FAILED"


class AlertRuleBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    metric_type: MetricType
    operator: AlertOperator
    threshold: float = Field(0.0)
    target_identifier: Optional[str] = Field(None, max_length=100)
    duration_seconds: int = Field(60, ge=0, le=86400)
    severity: AlertSeverity = AlertSeverity.WARNING
    is_enabled: bool = True
    environment_id: Optional[UUID] = None
    server_id: Optional[UUID] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Alert rule name cannot be empty")
        return v

    @field_validator("target_identifier")
    @classmethod
    def validate_target_identifier(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if not re.match(r"^[A-Za-z0-9_.@:-]+$", v):
                raise ValueError("Invalid target identifier format")
        return v

    @model_validator(mode="after")
    def validate_threshold_for_metric(self):
        # Validation for percentage thresholds
        if self.metric_type in (
            MetricType.CPU_USAGE,
            MetricType.MEMORY_USAGE,
            MetricType.DISK_USAGE,
        ):
            if not (0.0 <= self.threshold <= 100.0):
                raise ValueError(
                    f"Threshold for {self.metric_type.value} must be between 0 and 100"
                )
        return self


class AlertRuleCreate(AlertRuleBase):
    pass


class AlertRuleUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    metric_type: Optional[MetricType] = None
    operator: Optional[AlertOperator] = None
    threshold: Optional[float] = None
    target_identifier: Optional[str] = Field(None, max_length=100)
    duration_seconds: Optional[int] = Field(None, ge=0, le=86400)
    severity: Optional[AlertSeverity] = None
    is_enabled: Optional[bool] = None
    environment_id: Optional[UUID] = None
    server_id: Optional[UUID] = None


class AlertRuleResponse(AlertRuleBase):
    id: UUID
    workspace_id: UUID
    environment_name: Optional[str] = None
    server_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AlertEventResponse(BaseModel):
    id: UUID
    alert_id: UUID
    event_type: str
    message: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AlertResponse(BaseModel):
    id: UUID
    workspace_id: UUID
    alert_rule_id: UUID
    alert_rule_name: Optional[str] = None
    environment_id: Optional[UUID] = None
    environment_name: Optional[str] = None
    server_id: Optional[UUID] = None
    server_name: Optional[str] = None
    status: str
    severity: str
    title: str
    message: str
    current_value: Optional[float] = None
    threshold_value: Optional[float] = None
    triggered_at: datetime
    resolved_at: Optional[datetime] = None
    last_evaluated_at: datetime
    notification_sent_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AlertDetailResponse(AlertResponse):
    events: List[AlertEventResponse] = []


class AlertResolveRequest(BaseModel):
    confirm: bool = Field(..., description="Confirmation flag to resolve the alert")


class NotificationPreferenceUpdate(BaseModel):
    in_app_enabled: Optional[bool] = None
    email_enabled: Optional[bool] = None
    minimum_severity: Optional[AlertSeverity] = None


class NotificationPreferenceResponse(BaseModel):
    id: UUID
    user_id: UUID
    workspace_id: UUID
    in_app_enabled: bool
    email_enabled: bool
    minimum_severity: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NotificationResponse(BaseModel):
    id: UUID
    user_id: UUID
    workspace_id: UUID
    alert_id: Optional[UUID] = None
    title: str
    message: str
    severity: str
    is_read: bool
    read_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UnreadNotificationCountResponse(BaseModel):
    workspace_id: UUID
    unread_count: int


class AlertEvaluationSummary(BaseModel):
    rules_evaluated: int
    alerts_triggered: int
    alerts_resolved: int
    notifications_sent: int
    errors: List[str] = []
