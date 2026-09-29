import uuid
import secrets
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.agent import Agent, AgentEnrollmentToken, AgentJob
from app.models.server import Server
from app.services.audit_service import AuditService


class AgentManager:
    OFFLINE_THRESHOLD_SECONDS = 90

    @staticmethod
    def hash_token(raw_token: str) -> str:
        return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()

    @staticmethod
    def _hash_token(raw_token: str) -> str:
        return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()

    @classmethod
    def create_enrollment_token(
        cls,
        db: Session,
        workspace_id: uuid.UUID,
        server_id: uuid.UUID,
        user_id: Optional[uuid.UUID] = None,
        expires_in_minutes: int = 15,
        backend_url: str = "http://127.0.0.1:8000",
    ) -> Tuple[AgentEnrollmentToken, str, str]:
        # Validate server exists in workspace
        server = db.execute(
            select(Server).where(
                Server.id == server_id,
                Server.workspace_id == workspace_id,
            )
        ).scalar_one_or_none()

        if not server:
            raise ValueError(f"Server {server_id} tidak ditemukan dalam workspace.")

        # Generate single-use secure random token
        raw_token = f"doh_enroll_{secrets.token_urlsafe(32)}"
        token_hash = cls.hash_token(raw_token)
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=expires_in_minutes)

        token_obj = AgentEnrollmentToken(
            workspace_id=workspace_id,
            server_id=server_id,
            token_hash=token_hash,
            expires_at=expires_at,
            created_by=user_id,
        )
        db.add(token_obj)
        db.commit()
        db.refresh(token_obj)

        installer_command = (
            f"sudo /opt/devops-agent/venv/bin/python -m agent.main enroll --server {backend_url} --token {raw_token} --config /etc/devops-agent/config.json"
        )

        AuditService(db).log(
            action="CREATE_AGENT_ENROLLMENT",
            resource_type="agent_enrollment_token",
            resource_id=str(token_obj.id),
            workspace_id=workspace_id,
            user_id=user_id,
            server_id=server_id,
            status="SUCCESS",
            metadata={"expires_in_minutes": expires_in_minutes},
        )

        return token_obj, raw_token, installer_command

    @classmethod
    def enroll_agent(
        cls,
        db: Session,
        enrollment_token: str,
        hostname: Optional[str] = None,
        operating_system: Optional[str] = None,
        architecture: Optional[str] = None,
        agent_version: str = "1.0.0",
        capabilities: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Agent, str]:
        token_hash = cls._hash_token(enrollment_token.strip())
        now = datetime.now(timezone.utc)

        token_obj = db.execute(
            select(AgentEnrollmentToken).where(
                AgentEnrollmentToken.token_hash == token_hash
            )
        ).scalar_one_or_none()

        if not token_obj:
            raise ValueError("Enrollment token tidak valid.")

        if token_obj.used_at is not None:
            raise ValueError("Enrollment token sudah pernah digunakan (single-use).")

        expires_at = token_obj.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        if expires_at < now:
            raise ValueError("Enrollment token sudah kadaluarsa.")

        # Mark token as used immediately
        token_obj.used_at = now

        server = db.execute(
            select(Server).where(Server.id == token_obj.server_id)
        ).scalar_one_or_none()

        if not server:
            raise ValueError("Server target enrollment tidak ditemukan.")

        # Find or create agent for this server
        agent = db.execute(
            select(Agent).where(Agent.server_id == server.id)
        ).scalar_one_or_none()

        raw_agent_token = f"doh_agent_{secrets.token_urlsafe(32)}"
        agent_token_hash = cls._hash_token(raw_agent_token)

        if not agent:
            agent = Agent(
                server_id=server.id,
                workspace_id=server.workspace_id,
                name=f"Agent-{server.name}",
                agent_version=agent_version,
                status="ONLINE",
                auth_token_hash=agent_token_hash,
                last_seen_at=now,
                connected_at=now,
                hostname=hostname,
                operating_system=operating_system,
                architecture=architecture,
                capabilities=capabilities or {},
                is_active=True,
            )
            db.add(agent)
        else:
            agent.name = f"Agent-{server.name}"
            agent.agent_version = agent_version
            agent.status = "ONLINE"
            agent.auth_token_hash = agent_token_hash
            agent.last_seen_at = now
            agent.connected_at = now
            agent.hostname = hostname
            agent.operating_system = operating_system
            agent.architecture = architecture
            agent.capabilities = capabilities or {}
            agent.is_active = True

        # Switch server connection mode to AGENT
        server.connection_type = "AGENT"

        db.commit()
        db.refresh(agent)

        AuditService(db).log(
            action="AGENT_ENROLLED",
            resource_type="agent",
            resource_id=str(agent.id),
            workspace_id=server.workspace_id,
            server_id=server.id,
            status="SUCCESS",
            metadata={
                "hostname": hostname,
                "os": operating_system,
                "agent_version": agent_version,
            },
        )

        return agent, raw_agent_token

    @classmethod
    def authenticate_agent(
        cls,
        db: Session,
        agent_id: uuid.UUID,
        agent_token: str,
    ) -> Optional[Agent]:
        token_hash = cls.hash_token(agent_token.strip())
        agent = db.execute(
            select(Agent).where(
                Agent.id == agent_id,
                Agent.auth_token_hash == token_hash,
                Agent.is_active == True,
            )
        ).scalar_one_or_none()

        if not agent:
            return None

        agent.last_seen_at = datetime.now(timezone.utc)
        db.commit()
        return agent

    @classmethod
    def heartbeat(
        cls,
        db: Session,
        agent_id: uuid.UUID,
        agent_version: str = "1.0.0",
        hostname: Optional[str] = None,
        operating_system: Optional[str] = None,
        architecture: Optional[str] = None,
        capabilities: Optional[Dict[str, Any]] = None,
        status: str = "ONLINE",
    ) -> Agent:
        agent = db.execute(
            select(Agent).where(Agent.id == agent_id)
        ).scalar_one_or_none()

        if not agent:
            raise ValueError(f"Agent {agent_id} tidak ditemukan.")

        if not agent.is_active or agent.status == "DISABLED":
            raise ValueError(f"Agent {agent_id} telah dinonaktifkan.")

        agent.last_seen_at = datetime.now(timezone.utc)
        agent.status = status
        agent.agent_version = agent_version
        if hostname:
            agent.hostname = hostname
        if operating_system:
            agent.operating_system = operating_system
        if architecture:
            agent.architecture = architecture
        if capabilities is not None:
            agent.capabilities = capabilities

        db.commit()
        db.refresh(agent)
        return agent

    @classmethod
    def get_agent_for_server(
        cls,
        db: Session,
        workspace_id: uuid.UUID,
        server_id: uuid.UUID,
    ) -> Optional[Agent]:
        agent = db.execute(
            select(Agent).where(
                Agent.server_id == server_id,
                Agent.workspace_id == workspace_id,
            )
        ).scalar_one_or_none()

        if not agent:
            return None

        # Check offline staleness dynamically
        if agent.status == "ONLINE" and agent.last_seen_at:
            now = datetime.now(timezone.utc)
            last_seen = agent.last_seen_at
            if last_seen.tzinfo is None:
                last_seen = last_seen.replace(tzinfo=timezone.utc)
            delta = (now - last_seen).total_seconds()
            if delta > cls.OFFLINE_THRESHOLD_SECONDS:
                agent.status = "OFFLINE"
                db.commit()
                db.refresh(agent)

        return agent

    @classmethod
    def disable_agent(
        cls,
        db: Session,
        workspace_id: uuid.UUID,
        server_id: uuid.UUID,
        user_id: Optional[uuid.UUID] = None,
    ) -> Agent:
        agent = db.execute(
            select(Agent).where(
                Agent.server_id == server_id,
                Agent.workspace_id == workspace_id,
            )
        ).scalar_one_or_none()

        if not agent:
            raise ValueError("Agent tidak ditemukan.")

        agent.is_active = False
        agent.status = "DISABLED"
        agent.disconnected_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(agent)

        AuditService(db).log(
            action="DISABLE_AGENT",
            resource_type="agent",
            resource_id=str(agent.id),
            workspace_id=workspace_id,
            user_id=user_id,
            server_id=server_id,
            status="SUCCESS",
        )

        return agent

    @classmethod
    def revoke_agent(
        cls,
        db: Session,
        workspace_id: uuid.UUID,
        server_id: uuid.UUID,
        user_id: Optional[uuid.UUID] = None,
    ) -> Agent:
        agent = db.execute(
            select(Agent).where(
                Agent.server_id == server_id,
                Agent.workspace_id == workspace_id,
            )
        ).scalar_one_or_none()

        if not agent:
            raise ValueError("Agent tidak ditemukan.")

        server = db.execute(
            select(Server).where(Server.id == server_id)
        ).scalar_one_or_none()

        agent.auth_token_hash = None
        agent.is_active = False
        agent.status = "DISABLED"
        agent.disconnected_at = datetime.now(timezone.utc)

        if server:
            server.connection_type = "SSH"

        db.commit()
        db.refresh(agent)

        AuditService(db).log(
            action="REVOKE_AGENT",
            resource_type="agent",
            resource_id=str(agent.id),
            workspace_id=workspace_id,
            user_id=user_id,
            server_id=server_id,
            status="SUCCESS",
        )

        return agent
