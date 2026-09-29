import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional
from sqlalchemy import String, Integer, Boolean, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.workspace import Workspace
    from app.models.environment import Environment
    from app.models.server_credential import ServerCredential


class Server(Base):
    __tablename__ = "servers"

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
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    hostname: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    ip_address: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
    )
    ssh_port: Mapped[int] = mapped_column(
        Integer,
        default=22,
        nullable=False,
    )
    username: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
    )
    operating_system: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
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
    workspace: Mapped["Workspace"] = relationship(
        "Workspace",
        back_populates="servers",
    )
    environment: Mapped["Environment"] = relationship(
        "Environment",
        back_populates="servers",
    )
    credential: Mapped[Optional["ServerCredential"]] = relationship(
        "ServerCredential",
        back_populates="server",
        uselist=False,
        cascade="all, delete-orphan",
    )

    @validates("environment")
    def validate_environment(self, key: str, env: Optional["Environment"]):
        if env is not None and self.workspace_id is not None:
            if env.workspace_id != self.workspace_id:
                raise ValueError(
                    f"Environment '{env.id}' belongs to workspace '{env.workspace_id}', "
                    f"which does not match server workspace '{self.workspace_id}'."
                )
        return env

    def validate_workspace_environment(self) -> None:
        """Application-level cross-validation for workspace and environment consistency."""
        if self.environment is not None and self.workspace_id is not None:
            if self.environment.workspace_id != self.workspace_id:
                raise ValueError(
                    f"Environment '{self.environment.id}' belongs to workspace '{self.environment.workspace_id}', "
                    f"which does not match server workspace '{self.workspace_id}'."
                )

    def __repr__(self) -> str:
        return f"<Server(id={self.id}, name={self.name}, workspace_id={self.workspace_id})>"
