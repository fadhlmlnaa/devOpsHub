import asyncio
from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional, Tuple
import uuid
from fastapi import HTTPException, status
from sqlalchemy import select, and_, or_, func, desc
from sqlalchemy.orm import Session

from app.models.deployment import DeploymentConfig, Deployment, DeploymentLog
from app.models.environment import Environment
from app.models.server import Server
from app.models.server_credential import ServerCredential
from app.models.user import User
from app.models.workspace_member import WorkspaceMember, WorkspaceRole
from app.schemas.deployment import (
    DeploymentConfigCreate,
    DeploymentConfigUpdate,
    DeploymentConfigResponse,
    DeploymentResponse,
    DeploymentListResponse,
    DeploymentLogsResponse,
    DeploymentLogEntry,
)
from app.services.encryption import SecretEncryptionService
from app.services.redaction import secret_redactor
from app.infrastructure.deployment_providers.base import DeploymentProvider
from app.infrastructure.deployment_providers.ssh_deployment import SSHDeploymentProvider

logger = logging.getLogger(__name__)


class DeploymentManagementService:
    """Service orchestrating deployment configurations, executions, concurrency locking, and logging."""

    def __init__(
        self,
        db: Session,
        provider: Optional[DeploymentProvider] = None,
        encryption_service: Optional[SecretEncryptionService] = None,
    ):
        self.db = db
        self.provider = provider or SSHDeploymentProvider()
        self.encryption = encryption_service or SecretEncryptionService()

    # --- Authorization & Scope Helpers ---

    def _verify_workspace_membership(
        self, workspace_id: uuid.UUID, member: WorkspaceMember, required_mutation: bool = False
    ):
        if member.workspace_id != workspace_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Anda tidak memiliki akses ke workspace ini.",
            )
        if required_mutation and member.role not in [WorkspaceRole.ADMIN, WorkspaceRole.OWNER]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Hanya ADMIN dan OWNER yang memiliki izin untuk memodifikasi atau mengeksekusi deployment.",
            )

    def _get_scoped_server(self, workspace_id: uuid.UUID, server_id: uuid.UUID) -> Server:
        server = (
            self.db.query(Server)
            .filter(and_(Server.id == server_id, Server.workspace_id == workspace_id))
            .first()
        )
        if not server:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Server tidak ditemukan atau tidak berada di workspace yang sesuai.",
            )
        return server

    def _get_scoped_environment(self, workspace_id: uuid.UUID, environment_id: uuid.UUID) -> Environment:
        env = (
            self.db.query(Environment)
            .filter(and_(Environment.id == environment_id, Environment.workspace_id == workspace_id))
            .first()
        )
        if not env:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Environment tidak ditemukan atau tidak berada di workspace yang sesuai.",
            )
        return env

    def _get_scoped_config(self, workspace_id: uuid.UUID, config_id: uuid.UUID) -> DeploymentConfig:
        cfg = (
            self.db.query(DeploymentConfig)
            .filter(and_(DeploymentConfig.id == config_id, DeploymentConfig.workspace_id == workspace_id))
            .first()
        )
        if not cfg:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Deployment configuration tidak ditemukan di workspace ini.",
            )
        return cfg

    # --- Deployment Config CRUD ---

    def list_deployment_configs(
        self,
        workspace_id: uuid.UUID,
        member: WorkspaceMember,
        environment_id: Optional[uuid.UUID] = None,
        server_id: Optional[uuid.UUID] = None,
    ) -> List[DeploymentConfigResponse]:
        self._verify_workspace_membership(workspace_id, member, required_mutation=False)

        query = self.db.query(DeploymentConfig).filter(DeploymentConfig.workspace_id == workspace_id)
        if environment_id:
            query = query.filter(DeploymentConfig.environment_id == environment_id)
        if server_id:
            query = query.filter(DeploymentConfig.server_id == server_id)

        configs = query.order_by(DeploymentConfig.name.asc()).all()
        results = []
        for c in configs:
            env = c.environment
            srv = c.server
            data = DeploymentConfigResponse.model_validate(c)
            data.environment_name = env.name if env else None
            data.environment_is_protected = env.is_protected if env else False
            data.server_name = srv.name if srv else None
            results.append(data)
        return results

    def get_deployment_config(
        self, workspace_id: uuid.UUID, config_id: uuid.UUID, member: WorkspaceMember
    ) -> DeploymentConfigResponse:
        self._verify_workspace_membership(workspace_id, member, required_mutation=False)
        c = self._get_scoped_config(workspace_id, config_id)
        data = DeploymentConfigResponse.model_validate(c)
        data.environment_name = c.environment.name if c.environment else None
        data.environment_is_protected = c.environment.is_protected if c.environment else False
        data.server_name = c.server.name if c.server else None
        return data

    def create_deployment_config(
        self, workspace_id: uuid.UUID, data: DeploymentConfigCreate, member: WorkspaceMember
    ) -> DeploymentConfigResponse:
        self._verify_workspace_membership(workspace_id, member, required_mutation=True)

        env = self._get_scoped_environment(workspace_id, data.environment_id)
        srv = self._get_scoped_server(workspace_id, data.server_id)

        # Ensure server belongs to same environment if server has environment_id
        if srv.environment_id != env.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Server yang dipilih tidak terhubung dengan Environment yang dipilih.",
            )

        pre_steps = [s.model_dump() if hasattr(s, "model_dump") else s for s in data.pre_deploy_steps or []]
        dep_steps = [s.model_dump() if hasattr(s, "model_dump") else s for s in data.deploy_steps or []]
        post_steps = [s.model_dump() if hasattr(s, "model_dump") else s for s in data.post_deploy_steps or []]

        config = DeploymentConfig(
            workspace_id=workspace_id,
            environment_id=env.id,
            server_id=srv.id,
            name=data.name.strip(),
            description=data.description,
            application_name=data.application_name.strip(),
            working_directory=data.working_directory.strip(),
            deployment_type=data.deployment_type.value if hasattr(data.deployment_type, "value") else data.deployment_type,
            branch=data.branch.strip() if data.branch else None,
            repository_url=data.repository_url.strip() if data.repository_url else None,
            pre_deploy_steps=pre_steps,
            deploy_steps=dep_steps,
            post_deploy_steps=post_steps,
            restart_service_name=data.restart_service_name.strip() if data.restart_service_name else None,
            compose_project_name=data.compose_project_name.strip() if data.compose_project_name else None,
            health_check_type=data.health_check_type.value if hasattr(data.health_check_type, "value") else data.health_check_type,
            health_check_url=data.health_check_url.strip() if data.health_check_url else None,
            is_active=data.is_active,
        )
        self.db.add(config)
        self.db.commit()
        self.db.refresh(config)

        res = DeploymentConfigResponse.model_validate(config)
        res.environment_name = env.name
        res.environment_is_protected = env.is_protected
        res.server_name = srv.name
        return res

    def update_deployment_config(
        self, workspace_id: uuid.UUID, config_id: uuid.UUID, data: DeploymentConfigUpdate, member: WorkspaceMember
    ) -> DeploymentConfigResponse:
        self._verify_workspace_membership(workspace_id, member, required_mutation=True)
        config = self._get_scoped_config(workspace_id, config_id)

        update_dict = data.model_dump(exclude_unset=True)
        for key, val in update_dict.items():
            if key in ["pre_deploy_steps", "deploy_steps", "post_deploy_steps"] and val is not None:
                val = [s.model_dump() if hasattr(s, "model_dump") else s for s in val]
            elif hasattr(val, "value"):
                val = val.value
            setattr(config, key, val)

        self.db.commit()
        self.db.refresh(config)

        res = DeploymentConfigResponse.model_validate(config)
        res.environment_name = config.environment.name if config.environment else None
        res.environment_is_protected = config.environment.is_protected if config.environment else False
        res.server_name = config.server.name if config.server else None
        return res

    def delete_deployment_config(
        self, workspace_id: uuid.UUID, config_id: uuid.UUID, member: WorkspaceMember
    ) -> Dict[str, Any]:
        self._verify_workspace_membership(workspace_id, member, required_mutation=True)
        config = self._get_scoped_config(workspace_id, config_id)

        # Check if currently active running deployment
        running = (
            self.db.query(Deployment)
            .filter(and_(Deployment.deployment_config_id == config_id, Deployment.status == "RUNNING"))
            .first()
        )
        if running:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Tidak dapat menghapus konfigurasi deployment karena ada deployment yang sedang berjalan.",
            )

        self.db.delete(config)
        self.db.commit()
        return {"success": True, "message": "Deployment configuration deleted successfully."}

    # --- Deployment Execution & Concurrency Locking ---

    async def trigger_deployment(
        self,
        workspace_id: uuid.UUID,
        config_id: uuid.UUID,
        member: WorkspaceMember,
        user_id: uuid.UUID,
        confirm: bool,
    ) -> DeploymentResponse:
        self._verify_workspace_membership(workspace_id, member, required_mutation=True)
        config = self._get_scoped_config(workspace_id, config_id)

        if not config.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Konfigurasi deployment sedang non-aktif.",
            )

        env = config.environment
        if not env:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Environment tidak ditemukan.")

        # Protected Environment Confirmation Check
        if not confirm:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Konfirmasi eksekusi deployment diperlukan (confirm=true).",
            )

        # Concurrency Lock Check
        active_deployment = (
            self.db.query(Deployment)
            .filter(
                and_(
                    Deployment.deployment_config_id == config_id,
                    Deployment.status == "RUNNING",
                )
            )
            .first()
        )
        if active_deployment:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Deployment sedang berjalan untuk konfigurasi ini. Harap tunggu hingga selesai.",
            )

        srv = config.server
        if not srv:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Target server tidak ditemukan.")

        cred = self.db.query(ServerCredential).filter(ServerCredential.server_id == srv.id).first()
        if not cred:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Kredensial SSH server target belum dikonfigurasi.",
            )

        password = self.encryption.decrypt(cred.encrypted_password) if cred.encrypted_password else None
        pk = self.encryption.decrypt(cred.encrypted_private_key) if cred.encrypted_private_key else None
        passphrase = self.encryption.decrypt(cred.encrypted_passphrase) if cred.encrypted_passphrase else None
        host = srv.ip_address or srv.hostname
        if not host:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Host / IP server tidak valid.")

        # Create Deployment record with RUNNING state
        now = datetime.now(timezone.utc)
        deployment = Deployment(
            workspace_id=workspace_id,
            environment_id=env.id,
            server_id=srv.id,
            deployment_config_id=config.id,
            status="RUNNING",
            triggered_by_user_id=user_id,
            started_at=now,
            message="Deployment dimulai...",
        )
        self.db.add(deployment)
        self.db.commit()
        self.db.refresh(deployment)

        try:
            # Execute deployment through provider
            exec_result = await self.provider.deploy(
                host=host,
                port=srv.ssh_port,
                username=cred.username,
                password=password,
                private_key=pk,
                passphrase=passphrase,
                config=config,
            )

            deployment.status = exec_result.status
            deployment.finished_at = datetime.now(timezone.utc)
            deployment.commit_reference = exec_result.commit_reference
            deployment.message = exec_result.message
            deployment.error_message = exec_result.error_message

            # Save persisted logs
            for entry in exec_result.logs:
                ts = entry.get("timestamp")
                if isinstance(ts, str):
                    try:
                        ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                    except Exception:
                        ts = datetime.now(timezone.utc)
                elif not isinstance(ts, datetime):
                    ts = datetime.now(timezone.utc)

                raw_msg = entry.get("message", "")
                cleaned_msg = secret_redactor.redact(raw_msg)

                log_row = DeploymentLog(
                    deployment_id=deployment.id,
                    sequence=entry["sequence"],
                    timestamp=ts,
                    level=entry["level"],
                    message=cleaned_msg,
                )
                self.db.add(log_row)

            self.db.commit()
            self.db.refresh(deployment)

        except Exception as e:
            logger.error("Unexpected error during deployment execution: %s", e)
            deployment.status = "FAILED"
            deployment.finished_at = datetime.now(timezone.utc)
            deployment.error_message = str(e)
            deployment.message = "Terjadi kegagalan saat mengeksekusi deployment."
            self.db.commit()
            self.db.refresh(deployment)

        user_name = None
        if deployment.triggered_by_user_id:
            user = self.db.query(User).filter(User.id == deployment.triggered_by_user_id).first()
            user_name = user.name if user else None

        res = DeploymentResponse.model_validate(deployment)
        res.deployment_config_name = config.name
        res.environment_name = env.name
        res.environment_is_protected = env.is_protected
        res.server_name = srv.name
        res.triggered_by_name = user_name
        return res

    # --- Deployment History & Logs Retrieval ---

    def list_deployments(
        self,
        workspace_id: uuid.UUID,
        member: WorkspaceMember,
        environment_id: Optional[uuid.UUID] = None,
        server_id: Optional[uuid.UUID] = None,
        deployment_config_id: Optional[uuid.UUID] = None,
        status_filter: Optional[str] = None,
        page: int = 1,
        limit: int = 20,
    ) -> DeploymentListResponse:
        self._verify_workspace_membership(workspace_id, member, required_mutation=False)

        query = self.db.query(Deployment).filter(Deployment.workspace_id == workspace_id)
        if environment_id:
            query = query.filter(Deployment.environment_id == environment_id)
        if server_id:
            query = query.filter(Deployment.server_id == server_id)
        if deployment_config_id:
            query = query.filter(Deployment.deployment_config_id == deployment_config_id)
        if status_filter and status_filter.upper() != "ALL":
            query = query.filter(Deployment.status == status_filter.upper())

        total = query.count()
        offset = (page - 1) * limit
        deployments = query.order_by(desc(Deployment.created_at)).offset(offset).limit(limit).all()

        items = []
        for d in deployments:
            user_name = d.triggered_by.name if d.triggered_by else None
            cfg_name = d.deployment_config.name if d.deployment_config else None
            env_name = d.environment.name if d.environment else None
            env_prot = d.environment.is_protected if d.environment else False
            srv_name = d.server.name if d.server else None

            item = DeploymentResponse.model_validate(d)
            item.triggered_by_name = user_name
            item.deployment_config_name = cfg_name
            item.environment_name = env_name
            item.environment_is_protected = env_prot
            item.server_name = srv_name
            items.append(item)

        return DeploymentListResponse(items=items, total=total, page=page, limit=limit)

    def get_deployment(
        self, workspace_id: uuid.UUID, deployment_id: uuid.UUID, member: WorkspaceMember
    ) -> DeploymentResponse:
        self._verify_workspace_membership(workspace_id, member, required_mutation=False)

        d = (
            self.db.query(Deployment)
            .filter(and_(Deployment.id == deployment_id, Deployment.workspace_id == workspace_id))
            .first()
        )
        if not d:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deployment tidak ditemukan.")

        res = DeploymentResponse.model_validate(d)
        res.triggered_by_name = d.triggered_by.name if d.triggered_by else None
        res.deployment_config_name = d.deployment_config.name if d.deployment_config else None
        res.environment_name = d.environment.name if d.environment else None
        res.environment_is_protected = d.environment.is_protected if d.environment else False
        res.server_name = d.server.name if d.server else None
        return res

    def get_deployment_logs(
        self,
        workspace_id: uuid.UUID,
        deployment_id: uuid.UUID,
        member: WorkspaceMember,
        lines: int = 100,
    ) -> DeploymentLogsResponse:
        self._verify_workspace_membership(workspace_id, member, required_mutation=False)

        d = (
            self.db.query(Deployment)
            .filter(and_(Deployment.id == deployment_id, Deployment.workspace_id == workspace_id))
            .first()
        )
        if not d:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deployment tidak ditemukan.")

        limit_lines = max(10, min(lines, 1000))
        logs_query = (
            self.db.query(DeploymentLog)
            .filter(DeploymentLog.deployment_id == deployment_id)
            .order_by(DeploymentLog.sequence.asc())
            .limit(limit_lines)
            .all()
        )

        entries = [
            DeploymentLogEntry(
                sequence=l.sequence,
                timestamp=l.timestamp,
                level=l.level,
                message=l.message,
            )
            for l in logs_query
        ]

        return DeploymentLogsResponse(
            deployment_id=d.id,
            status=d.status,
            lines_returned=len(entries),
            entries=entries,
        )
