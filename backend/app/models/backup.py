import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional
from sqlalchemy import (
    String,
    Text,
    DateTime,
    ForeignKey,
    Boolean,
    Integer,
    BigInteger,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.workspace import Workspace
    from app.models.environment import Environment
    from app.models.server import Server
    from app.models.user import User


class BackupConfig(Base):
    __tablename__ = "backup_configs"

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
    backup_type: Mapped[str] = mapped_column(
        String(64),
        default="POSTGRESQL",
        nullable=False,
    )  # "POSTGRESQL", "FILESYSTEM", "DOCKER_VOLUME"
    source: Mapped[str] = mapped_column(
        String(1024),
        nullable=False,
    )  # db name, directory path, or docker volume name
    destination: Mapped[str] = mapped_column(
        String(1024),
        nullable=False,
    )  # backup destination directory on target server
    retention_days: Mapped[int] = mapped_column(
        Integer,
        default=7,
        nullable=False,
    )
    is_compressed: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
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
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    workspace: Mapped["Workspace"] = relationship("Workspace", lazy="joined")
    environment: Mapped["Environment"] = relationship("Environment", lazy="joined")
    server: Mapped["Server"] = relationship("Server", lazy="joined")
    backups: Mapped[list["Backup"]] = relationship(
        "Backup",
        back_populates="backup_config",
        cascade="all, delete-orphan",
        order_by="desc(Backup.created_at)",
    )


class Backup(Base):
    __tablename__ = "backups"

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
    backup_config_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("backup_configs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(64),
        default="PENDING",
        nullable=False,
        index=True,
    )  # "PENDING", "RUNNING", "SUCCESS", "FAILED", "CANCELLED"
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    finished_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    file_name: Mapped[Optional[str]] = mapped_column(
        String(512),
        nullable=True,
    )
    file_path: Mapped[Optional[str]] = mapped_column(
        String(1024),
        nullable=True,
    )
    file_size_bytes: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        nullable=True,
    )
    checksum: Mapped[Optional[str]] = mapped_column(
        String(128),
        nullable=True,
    )  # SHA-256
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    triggered_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    # Relationships
    workspace: Mapped["Workspace"] = relationship("Workspace", lazy="joined")
    environment: Mapped["Environment"] = relationship("Environment", lazy="joined")
    server: Mapped["Server"] = relationship("Server", lazy="joined")
    backup_config: Mapped["BackupConfig"] = relationship("BackupConfig", back_populates="backups", lazy="joined")
    triggered_by: Mapped[Optional["User"]] = relationship("User", lazy="joined")
    logs: Mapped[list["BackupLog"]] = relationship(
        "BackupLog",
        back_populates="backup",
        cascade="all, delete-orphan",
        order_by="asc(BackupLog.sequence)",
    )


class BackupLog(Base):
    __tablename__ = "backup_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    backup_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("backups.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sequence: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
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
    backup: Mapped["Backup"] = relationship("Backup", back_populates="logs")
