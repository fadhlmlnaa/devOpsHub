import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional
from sqlalchemy import String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.server import Server


class ServerCredential(Base):
    __tablename__ = "server_credentials"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    server_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("servers.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    auth_type: Mapped[str] = mapped_column(
        String(32),
        default="PASSWORD",
        nullable=False,
    )  # "PASSWORD" or "PRIVATE_KEY"
    username: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )
    encrypted_password: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    encrypted_private_key: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    encrypted_passphrase: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
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
    server: Mapped["Server"] = relationship(
        "Server",
        back_populates="credential",
    )

    def __repr__(self) -> str:
        return f"<ServerCredential(id={self.id}, server_id={self.server_id}, auth_type={self.auth_type})>"
