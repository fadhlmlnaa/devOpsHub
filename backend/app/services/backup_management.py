from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional
import uuid
from fastapi import HTTPException, status
from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.core.config import settings
from app.infrastructure.backup_providers import (
    BackupProvider,
    SSHBackupProvider,
    BackupExecutionResult,
    BackupVerificationResult,
)
from app.models.backup import BackupConfig, Backup, BackupLog
from app.models.environment import Environment
from app.models.server import Server
from app.models.server_credential import ServerCredential
from app.models.user import User
from app.models.workspace_member import WorkspaceMember, WorkspaceRole
from app.schemas.backup import (
    BackupConfigCreate,
    BackupConfigUpdate,
    BackupConfigResponse,
    BackupResponse,
    BackupListResponse,
    BackupLogEntry,
    BackupLogsResponse,
    BackupVerifyResponse,
)
from app.services.encryption import SecretEncryptionService
from app.services.redaction import secret_redactor
from app.services.provider_factory import ProviderFactory

logger = logging.getLogger(__name__)


class BackupManagementService:
    """Service layer managing backup configurations, controlled executions, verification, and history."""

    def __init__(
        self,
        db: Session,
        provider: Optional[BackupProvider] = None,
        encryption: Optional[SecretEncryptionService] = None,
    ):
        self.db = db
        self._custom_provider = provider
        self.encryption = encryption or SecretEncryptionService()

    def _get_provider(self, server: Server) -> BackupProvider:
        if self._custom_provider:
            return self._custom_provider
        return ProviderFactory.get_backup_provider(server, self.db)

    def _verify_workspace_membership(
        self,
        workspace_id: uuid.UUID,
        member: WorkspaceMember,
        required_mutation: bool = False,
    ) -> None:
        if member.workspace_id != workspace_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Akses workspace ditolak. Pengguna bukan anggota workspace ini.",
            )
        if required_mutation and member.role not in (WorkspaceRole.OWNER, WorkspaceRole.ADMIN):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Operasi ini memerlukan role OWNER atau ADMIN.",
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

    def _get_scoped_config(self, workspace_id: uuid.UUID, config_id: uuid.UUID) -> BackupConfig:
        cfg = (
            self.db.query(BackupConfig)
            .filter(and_(BackupConfig.id == config_id, BackupConfig.workspace_id == workspace_id))
            .first()
        )
        if not cfg:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Konfigurasi backup tidak ditemukan di workspace ini.",
            )
        return cfg

    # --- Backup Config CRUD ---

    def list_backup_configs(
        self,
        workspace_id: uuid.UUID,
        member: WorkspaceMember,
        environment_id: Optional[uuid.UUID] = None,
        server_id: Optional[uuid.UUID] = None,
    ) -> List[BackupConfigResponse]:
        self._verify_workspace_membership(workspace_id, member, required_mutation=False)

        query = self.db.query(BackupConfig).filter(BackupConfig.workspace_id == workspace_id)
        if environment_id:
            query = query.filter(BackupConfig.environment_id == environment_id)
        if server_id:
            query = query.filter(BackupConfig.server_id == server_id)

        configs = query.order_by(BackupConfig.name.asc()).all()
        results = []
        for c in configs:
            env = c.environment
            srv = c.server
            data = BackupConfigResponse.model_validate(c)
            data.environment_name = env.name if env else None
            data.environment_is_protected = env.is_protected if env else False
            data.server_name = srv.name if srv else None
            results.append(data)
        return results

    def get_backup_config(
        self, workspace_id: uuid.UUID, config_id: uuid.UUID, member: WorkspaceMember
    ) -> BackupConfigResponse:
        self._verify_workspace_membership(workspace_id, member, required_mutation=False)
        c = self._get_scoped_config(workspace_id, config_id)
        data = BackupConfigResponse.model_validate(c)
        data.environment_name = c.environment.name if c.environment else None
        data.environment_is_protected = c.environment.is_protected if c.environment else False
        data.server_name = c.server.name if c.server else None
        return data

    def create_backup_config(
        self, workspace_id: uuid.UUID, data: BackupConfigCreate, member: WorkspaceMember
    ) -> BackupConfigResponse:
        self._verify_workspace_membership(workspace_id, member, required_mutation=True)

        env = self._get_scoped_environment(workspace_id, data.environment_id)
        srv = self._get_scoped_server(workspace_id, data.server_id)

        if srv.environment_id != env.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Server yang dipilih tidak berada di environment yang ditentukan.",
            )

        # Check duplicate name in workspace
        dup = (
            self.db.query(BackupConfig)
            .filter(and_(BackupConfig.workspace_id == workspace_id, BackupConfig.name == data.name))
            .first()
        )
        if dup:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Konfigurasi backup dengan nama '{data.name}' sudah terdaftar di workspace ini.",
            )

        config = BackupConfig(
            workspace_id=workspace_id,
            environment_id=env.id,
            server_id=srv.id,
            name=data.name,
            description=data.description,
            backup_type=data.backup_type.value if hasattr(data.backup_type, "value") else str(data.backup_type),
            source=data.source,
            destination=data.destination,
            retention_days=data.retention_days,
            is_compressed=data.is_compressed,
            is_active=data.is_active,
        )
        self.db.add(config)
        self.db.commit()
        self.db.refresh(config)

        res = BackupConfigResponse.model_validate(config)
        res.environment_name = env.name
        res.environment_is_protected = env.is_protected
        res.server_name = srv.name
        return res

    def update_backup_config(
        self, workspace_id: uuid.UUID, config_id: uuid.UUID, data: BackupConfigUpdate, member: WorkspaceMember
    ) -> BackupConfigResponse:
        self._verify_workspace_membership(workspace_id, member, required_mutation=True)
        config = self._get_scoped_config(workspace_id, config_id)

        update_dict = data.model_dump(exclude_unset=True)
        if "name" in update_dict and update_dict["name"] != config.name:
            dup = (
                self.db.query(BackupConfig)
                .filter(
                    and_(
                        BackupConfig.workspace_id == workspace_id,
                        BackupConfig.name == update_dict["name"],
                        BackupConfig.id != config_id,
                    )
                )
                .first()
            )
            if dup:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Konfigurasi backup dengan nama '{update_dict['name']}' sudah ada.",
                )

        for key, val in update_dict.items():
            setattr(config, key, val)

        self.db.commit()
        self.db.refresh(config)

        res = BackupConfigResponse.model_validate(config)
        res.environment_name = config.environment.name if config.environment else None
        res.environment_is_protected = config.environment.is_protected if config.environment else False
        res.server_name = config.server.name if config.server else None
        return res

    def delete_backup_config(
        self, workspace_id: uuid.UUID, config_id: uuid.UUID, member: WorkspaceMember
    ) -> Dict[str, Any]:
        self._verify_workspace_membership(workspace_id, member, required_mutation=True)
        config = self._get_scoped_config(workspace_id, config_id)

        running = (
            self.db.query(Backup)
            .filter(and_(Backup.backup_config_id == config_id, Backup.status == "RUNNING"))
            .first()
        )
        if running:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Tidak dapat menghapus konfigurasi backup karena ada backup yang sedang berjalan.",
            )

        self.db.delete(config)
        self.db.commit()
        return {"success": True, "message": "Konfigurasi backup berhasil dihapus."}

    # --- Backup Execution & Verification ---

    async def trigger_backup(
        self,
        workspace_id: uuid.UUID,
        config_id: uuid.UUID,
        member: WorkspaceMember,
        user_id: uuid.UUID,
        confirm: bool,
    ) -> BackupResponse:
        self._verify_workspace_membership(workspace_id, member, required_mutation=True)
        config = self._get_scoped_config(workspace_id, config_id)

        if not config.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Konfigurasi backup sedang non-aktif.",
            )

        env = config.environment
        if not env:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Environment tidak ditemukan.")

        if not confirm:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Konfirmasi eksekusi backup diperlukan (confirm=true).",
            )

        # Concurrency Lock Check
        active_backup = (
            self.db.query(Backup)
            .filter(
                and_(
                    Backup.backup_config_id == config_id,
                    Backup.status == "RUNNING",
                )
            )
            .first()
        )
        if active_backup:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Backup sedang berjalan untuk konfigurasi ini. Harap tunggu hingga selesai.",
            )

        srv = config.server
        if not srv or not srv.is_active:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Server target tidak aktif atau tidak ditemukan.")

        password = None
        pk = None
        passphrase = None
        username = srv.username or "root"

        if srv.connection_type != "AGENT":
            cred = self.db.query(ServerCredential).filter(ServerCredential.server_id == srv.id).first()
            if not cred:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Kredensial SSH server target belum dikonfigurasi.",
                )
            username = cred.username
            password = self.encryption.decrypt(cred.encrypted_password) if cred.encrypted_password else None
            pk = self.encryption.decrypt(cred.encrypted_private_key) if cred.encrypted_private_key else None
            passphrase = self.encryption.decrypt(cred.encrypted_passphrase) if cred.encrypted_passphrase else None

        host = srv.ip_address or srv.hostname or ""

        # Create Backup record in RUNNING state
        now = datetime.now(timezone.utc)
        backup = Backup(
            workspace_id=workspace_id,
            environment_id=env.id,
            server_id=srv.id,
            backup_config_id=config.id,
            status="RUNNING",
            triggered_by_user_id=user_id,
            started_at=now,
        )
        self.db.add(backup)
        self.db.commit()
        self.db.refresh(backup)

        persisted_sequences = set()

        def on_log_entry(level: str, msg: str, sequence: int, ts: datetime):
            try:
                cleaned_msg = secret_redactor.redact(msg)
                log_row = BackupLog(
                    backup_id=backup.id,
                    sequence=sequence,
                    timestamp=ts,
                    level=level,
                    message=cleaned_msg,
                )
                self.db.add(log_row)
                self.db.commit()
                persisted_sequences.add(sequence)
            except Exception as ex:
                logger.warning("Failed to persist incremental backup log: %s", ex)

        try:
            provider = self._get_provider(srv)
            exec_result: BackupExecutionResult = await provider.execute(
                host=host,
                port=srv.ssh_port,
                username=username,
                password=password,
                private_key=pk,
                passphrase=passphrase,
                config=config,
                log_callback=on_log_entry,
            )

            backup.status = exec_result.status
            backup.finished_at = datetime.now(timezone.utc)
            backup.file_name = exec_result.file_name
            backup.file_path = exec_result.file_path
            backup.file_size_bytes = exec_result.file_size_bytes
            backup.checksum = exec_result.checksum
            backup.error_message = exec_result.error_message

            # Save any remaining logs
            if exec_result.logs:
                for entry in exec_result.logs:
                    if entry["sequence"] in persisted_sequences:
                        continue

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

                    log_row = BackupLog(
                        backup_id=backup.id,
                        sequence=entry["sequence"],
                        timestamp=ts,
                        level=entry["level"],
                        message=cleaned_msg,
                    )
                    self.db.add(log_row)

            self.db.commit()
            self.db.refresh(backup)

        except Exception as e:
            logger.error("Unexpected error during backup execution: %s", e)
            backup.status = "FAILED"
            backup.finished_at = datetime.now(timezone.utc)
            backup.error_message = str(e)
            self.db.commit()
            self.db.refresh(backup)

        user_name = None
        if backup.triggered_by_user_id:
            user = self.db.query(User).filter(User.id == backup.triggered_by_user_id).first()
            user_name = user.name if user else None

        res = BackupResponse.model_validate(backup)
        res.backup_config_name = config.name
        res.backup_type = config.backup_type
        res.environment_name = env.name
        res.environment_is_protected = env.is_protected
        res.server_name = srv.name
        res.triggered_by_name = user_name
        return res

    async def verify_backup(
        self,
        workspace_id: uuid.UUID,
        backup_id: uuid.UUID,
        member: WorkspaceMember,
        confirm: bool,
    ) -> BackupVerifyResponse:
        self._verify_workspace_membership(workspace_id, member, required_mutation=True)

        backup = (
            self.db.query(Backup)
            .filter(and_(Backup.id == backup_id, Backup.workspace_id == workspace_id))
            .first()
        )
        if not backup:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Backup tidak ditemukan.")

        if not backup.file_path:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File path backup tidak tersedia.")

        srv = backup.server
        if not srv or not srv.is_active:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Server target tidak aktif atau tidak ditemukan.")

        password = None
        pk = None
        passphrase = None
        username = srv.username or "root"

        if srv.connection_type != "AGENT":
            cred = self.db.query(ServerCredential).filter(ServerCredential.server_id == srv.id).first()
            if not cred:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Kredensial SSH server tidak ditemukan.")
            username = cred.username
            password = self.encryption.decrypt(cred.encrypted_password) if cred.encrypted_password else None
            pk = self.encryption.decrypt(cred.encrypted_private_key) if cred.encrypted_private_key else None
            passphrase = self.encryption.decrypt(cred.encrypted_passphrase) if cred.encrypted_passphrase else None

        host = srv.ip_address or srv.hostname or ""
        provider = self._get_provider(srv)

        v_result: BackupVerificationResult = await provider.verify(
            host=host,
            port=srv.ssh_port,
            username=username,
            password=password,
            private_key=pk,
            passphrase=passphrase,
            file_path=backup.file_path,
            expected_checksum=backup.checksum,
        )

        return BackupVerifyResponse(
            backup_id=backup.id,
            verified=v_result.verified,
            stored_checksum=v_result.stored_checksum,
            calculated_checksum=v_result.calculated_checksum,
            file_exists=v_result.file_exists,
            verified_at=datetime.now(timezone.utc),
            message=v_result.message,
        )

    # --- Backup History & Logs ---

    def list_backups(
        self,
        workspace_id: uuid.UUID,
        member: WorkspaceMember,
        environment_id: Optional[uuid.UUID] = None,
        server_id: Optional[uuid.UUID] = None,
        backup_config_id: Optional[uuid.UUID] = None,
        backup_type: Optional[str] = None,
        status_filter: Optional[str] = None,
        page: int = 1,
        limit: int = 20,
    ) -> BackupListResponse:
        self._verify_workspace_membership(workspace_id, member, required_mutation=False)

        query = self.db.query(Backup).filter(Backup.workspace_id == workspace_id)
        if environment_id:
            query = query.filter(Backup.environment_id == environment_id)
        if server_id:
            query = query.filter(Backup.server_id == server_id)
        if backup_config_id:
            query = query.filter(Backup.backup_config_id == backup_config_id)
        if status_filter:
            query = query.filter(Backup.status == status_filter.upper())
        if backup_type:
            query = query.join(BackupConfig).filter(BackupConfig.backup_type == backup_type.upper())

        total = query.count()
        offset = (page - 1) * limit
        backups = query.order_by(Backup.created_at.desc()).offset(offset).limit(limit).all()

        items = []
        for b in backups:
            item = BackupResponse.model_validate(b)
            item.backup_config_name = b.backup_config.name if b.backup_config else None
            item.backup_type = b.backup_config.backup_type if b.backup_config else None
            item.environment_name = b.environment.name if b.environment else None
            item.environment_is_protected = b.environment.is_protected if b.environment else False
            item.server_name = b.server.name if b.server else None
            item.triggered_by_name = b.triggered_by.name if b.triggered_by else None
            items.append(item)

        return BackupListResponse(
            total=total,
            page=page,
            limit=limit,
            items=items,
        )

    def get_backup(
        self, workspace_id: uuid.UUID, backup_id: uuid.UUID, member: WorkspaceMember
    ) -> BackupResponse:
        self._verify_workspace_membership(workspace_id, member, required_mutation=False)

        b = (
            self.db.query(Backup)
            .filter(and_(Backup.id == backup_id, Backup.workspace_id == workspace_id))
            .first()
        )
        if not b:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Backup tidak ditemukan.")

        res = BackupResponse.model_validate(b)
        res.backup_config_name = b.backup_config.name if b.backup_config else None
        res.backup_type = b.backup_config.backup_type if b.backup_config else None
        res.environment_name = b.environment.name if b.environment else None
        res.environment_is_protected = b.environment.is_protected if b.environment else False
        res.server_name = b.server.name if b.server else None
        res.triggered_by_name = b.triggered_by.name if b.triggered_by else None
        return res

    def get_backup_logs(
        self,
        workspace_id: uuid.UUID,
        backup_id: uuid.UUID,
        member: WorkspaceMember,
        lines: int = 100,
    ) -> BackupLogsResponse:
        self._verify_workspace_membership(workspace_id, member, required_mutation=False)

        b = (
            self.db.query(Backup)
            .filter(and_(Backup.id == backup_id, Backup.workspace_id == workspace_id))
            .first()
        )
        if not b:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Backup tidak ditemukan.")

        limit_lines = max(10, min(lines, 1000))
        logs_query = (
            self.db.query(BackupLog)
            .filter(BackupLog.backup_id == backup_id)
            .order_by(BackupLog.sequence.asc())
            .limit(limit_lines)
            .all()
        )

        entries = [
            BackupLogEntry(
                sequence=l.sequence,
                timestamp=l.timestamp,
                level=l.level,
                message=l.message,
            )
            for l in logs_query
        ]

        return BackupLogsResponse(
            backup_id=b.id,
            status=b.status,
            lines_returned=len(entries),
            entries=entries,
        )
