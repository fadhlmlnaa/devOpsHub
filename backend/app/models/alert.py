import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    String,
    Boolean,
    Float,
    Integer,
    DateTime,
    ForeignKey,
    Index,
    UniqueConstraint,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class AlertRule(Base):
    __tablename__ = "alert_rules"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    environment_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("environments.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    server_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("servers.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # CPU_USAGE, MEMORY_USAGE, DISK_USAGE, LOAD_AVERAGE, SERVER_STATUS, SERVICE_STATUS, DEPLOYMENT_STATUS, BACKUP_STATUS
    metric_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    # GREATER_THAN, GREATER_THAN_OR_EQUAL, LESS_THAN, LESS_THAN_OR_EQUAL, EQUAL, NOT_EQUAL
    operator: Mapped[str] = mapped_column(String(30), nullable=False)
    threshold: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    target_identifier: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    duration_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=60)
    # INFO, WARNING, CRITICAL
    severity: Mapped[str] = mapped_column(String(20), nullable=False, default="WARNING")
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    workspace = relationship("Workspace", backref="alert_rules")
    environment = relationship("Environment", backref="alert_rules")
    server = relationship("Server", backref="alert_rules")
    alerts = relationship(
        "Alert", back_populates="alert_rule", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_alert_rules_workspace_enabled", "workspace_id", "is_enabled"),
    )


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    alert_rule_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("alert_rules.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    environment_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("environments.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    server_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("servers.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # FIRING, RESOLVED
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="FIRING", index=True
    )
    # INFO, WARNING, CRITICAL
    severity: Mapped[str] = mapped_column(String(20), nullable=False, default="WARNING")

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)

    current_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    threshold_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    triggered_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_evaluated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    notification_sent_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    workspace = relationship("Workspace", backref="alerts")
    alert_rule = relationship("AlertRule", back_populates="alerts")
    environment = relationship("Environment", backref="alerts")
    server = relationship("Server", backref="alerts")
    events = relationship(
        "AlertEvent", back_populates="alert", cascade="all, delete-orphan"
    )
    notifications = relationship(
        "Notification", back_populates="alert", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_alerts_workspace_status", "workspace_id", "status"),
        Index("ix_alerts_rule_status", "alert_rule_id", "status"),
    )


class AlertEvent(Base):
    __tablename__ = "alert_events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    alert_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("alerts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # TRIGGERED, NOTIFICATION_SENT, RESOLVED, NOTIFICATION_FAILED
    event_type: Mapped[str] = mapped_column(String(30), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False, index=True
    )

    # Relationships
    alert = relationship("Alert", back_populates="events")


class NotificationPreference(Base):
    __tablename__ = "notification_preferences"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    in_app_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    email_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # INFO, WARNING, CRITICAL
    minimum_severity: Mapped[str] = mapped_column(
        String(20), nullable=False, default="INFO"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    user = relationship("User", backref="notification_preferences")
    workspace = relationship("Workspace", backref="notification_preferences")

    __table_args__ = (
        UniqueConstraint(
            "user_id", "workspace_id", name="uq_user_workspace_notification_pref"
        ),
    )


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    alert_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("alerts.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    # INFO, WARNING, CRITICAL
    severity: Mapped[str] = mapped_column(String(20), nullable=False, default="INFO")

    is_read: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, index=True
    )
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False, index=True
    )

    # Relationships
    user = relationship("User", backref="notifications")
    workspace = relationship("Workspace", backref="notifications")
    alert = relationship("Alert", back_populates="notifications")

    __table_args__ = (
        Index("ix_notifications_user_workspace_unread", "user_id", "workspace_id", "is_read"),
    )
