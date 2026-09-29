import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Dict, List, Optional
from sqlalchemy import (
    String,
    Text,
    DateTime,
    ForeignKey,
    Boolean,
    Integer,
    JSON,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.workspace import Workspace
    from app.models.environment import Environment
    from app.models.server import Server
    from app.models.user import User


class DeploymentConfig(Base):
    __tablename__ = "deployment_configs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    environment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("environments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    server_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("servers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    application_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    working_directory: Mapped[str] = mapped_column(
        String(1024),
        nullable=False,
    )
    deployment_type: Mapped[str] = mapped_column(
        String(64),
        default="SYSTEMD",
        nullable=False,
    )  # "SYSTEMD" or "DOCKER_COMPOSE"
    branch: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    repository_url: Mapped[Optional[str]] = mapped_column(
        String(1024),
        nullable=True,
    )
    pre_deploy_steps: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(
        JSON,
        nullable=True,
        default=list,
    )
    deploy_steps: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(
        JSON,
        nullable=True,
        default=list,
    )
    post_deploy_steps: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(
        JSON,
        nullable=True,
        default=list,
    )
    restart_service_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    compose_project_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    health_check_type: Mapped[Optional[str]] = mapped_column(
        String(64),
        default="NONE",
        nullable=True,
    )  # "NONE", "SERVICE_STATUS", "DOCKER_COMPOSE_STATUS", "HTTP_HEALTH_CHECK"
    health_check_url: Mapped[Optional[str]] = mapped_column(
        String(1024),
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    workspace: Mapped["Workspace"] = relationship("Workspace")
    environment: Mapped["Environment"] = relationship("Environment")
    server: Mapped["Server"] = relationship("Server")
    deployments: Mapped[List["Deployment"]] = relationship(
        "Deployment",
        back_populates="deployment_config",
        cascade="all, delete-orphan",
    )


class Deployment(Base):
    __tablename__ = "deployments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    environment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("environments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    server_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("servers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    deployment_config_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("deployment_configs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(64),
        default="PENDING",
        nullable=False,
        index=True,
    )  # "PENDING", "RUNNING", "SUCCESS", "FAILED", "CANCELLED"
    triggered_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    finished_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    commit_reference: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    workspace: Mapped["Workspace"] = relationship("Workspace")
    environment: Mapped["Environment"] = relationship("Environment")
    server: Mapped["Server"] = relationship("Server")
    deployment_config: Mapped["DeploymentConfig"] = relationship(
        "DeploymentConfig", back_populates="deployments"
    )
    triggered_by: Mapped[Optional["User"]] = relationship("User")
    logs: Mapped[List["DeploymentLog"]] = relationship(
        "DeploymentLog",
        back_populates="deployment",
        cascade="all, delete-orphan",
        order_by="DeploymentLog.sequence",
    )


class DeploymentLog(Base):
    __tablename__ = "deployment_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    deployment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("deployments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sequence: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    level: Mapped[str] = mapped_column(
        String(32),
        default="INFO",
        nullable=False,
    )  # "INFO", "WARNING", "ERROR"
    message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    # Relationship
    deployment: Mapped["Deployment"] = relationship("Deployment", back_populates="logs")
