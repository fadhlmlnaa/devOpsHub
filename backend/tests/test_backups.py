import uuid
from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient

from app.core.security import create_access_token
from app.infrastructure.backup_providers.base import (
    BackupProvider,
    BackupExecutionResult,
    BackupVerificationResult,
)
from app.models.backup import BackupConfig, Backup, BackupLog
from app.models.environment import Environment
from app.models.server import Server
from app.models.server_credential import ServerCredential
from app.models.user import User
from app.models.workspace import Workspace
from app.models.workspace_member import WorkspaceMember, WorkspaceRole
from app.services.backup_management import BackupManagementService
from app.services.encryption import SecretEncryptionService


class MockBackupProvider(BackupProvider):
    def __init__(self, succeed=True, checksum="a1b2c3d4e5f67890abcdef1234567890abcdef1234567890abcdef1234567890"):
        self.succeed = succeed
        self.checksum = checksum
        self.last_config = None

    async def validate_environment(self, host, port, username, password=None, private_key=None, passphrase=None, config=None):
        return True, "Valid"

    async def execute(self, host, port, username, password=None, private_key=None, passphrase=None, config=None, log_callback=None):
        self.last_config = config
        now = datetime.now(timezone.utc)
        if log_callback:
            log_callback("INFO", f"Connecting with password=super_secret_db_pass to {host}", 1, now)
            log_callback("INFO", "Executing pg_dump mydb > /var/backups/postgresql/mydb.sql.gz", 2, now)

        if not self.succeed:
            return BackupExecutionResult(
                success=False,
                status="FAILED",
                error_message="SSH connection timed out",
                logs=[
                    {"sequence": 1, "timestamp": now, "level": "INFO", "message": "Connecting..."},
                    {"sequence": 2, "timestamp": now, "level": "ERROR", "message": "SSH connection timed out"},
                ],
            )

        return BackupExecutionResult(
            success=True,
            status="SUCCESS",
            file_name=f"postgresql_{config.source}_2026-09-29.sql.gz",
            file_path=f"{config.destination}/postgresql_{config.source}_2026-09-29.sql.gz",
            file_size_bytes=1048576,
            checksum=self.checksum,
            logs=[
                {"sequence": 1, "timestamp": now, "level": "INFO", "message": "Connecting with password=super_secret_db_pass to server"},
                {"sequence": 2, "timestamp": now, "level": "INFO", "message": "Backup created successfully"},
            ],
        )

    async def verify(self, host, port, username, password=None, private_key=None, passphrase=None, file_path="", expected_checksum=None):
        if not self.succeed:
            return BackupVerificationResult(
                verified=False,
                file_exists=False,
                stored_checksum=expected_checksum,
                calculated_checksum=None,
                message="File not found on server",
            )

        if expected_checksum == self.checksum:
            return BackupVerificationResult(
                verified=True,
                file_exists=True,
                stored_checksum=expected_checksum,
                calculated_checksum=self.checksum,
                message="Verification successful. Checksum matches.",
            )
        else:
            return BackupVerificationResult(
                verified=False,
                file_exists=True,
                stored_checksum=expected_checksum,
                calculated_checksum="different_calculated_hash",
                message="Verification failed. Checksum mismatch.",
            )


@pytest.fixture
def setup_backup_env(db_session):
    """Sets up a workspace, environments, servers, credentials, and test users with roles."""
    enc = SecretEncryptionService()

    owner = User(email=f"owner-{uuid.uuid4().hex[:6]}@example.com", name="Owner", password_hash="pw")
    admin = User(email=f"admin-{uuid.uuid4().hex[:6]}@example.com", name="Admin", password_hash="pw")
    dev = User(email=f"dev-{uuid.uuid4().hex[:6]}@example.com", name="Dev", password_hash="pw")
    viewer = User(email=f"viewer-{uuid.uuid4().hex[:6]}@example.com", name="Viewer", password_hash="pw")
    other_user = User(email=f"other-{uuid.uuid4().hex[:6]}@example.com", name="Other", password_hash="pw")
    db_session.add_all([owner, admin, dev, viewer, other_user])
    db_session.commit()

    ws = Workspace(name="Backup WS", description="Backup Test Workspace")
    ws_other = Workspace(name="Other WS", description="Other Workspace")
    db_session.add_all([ws, ws_other])
    db_session.commit()

    m_owner = WorkspaceMember(workspace_id=ws.id, user_id=owner.id, role=WorkspaceRole.OWNER)
    m_admin = WorkspaceMember(workspace_id=ws.id, user_id=admin.id, role=WorkspaceRole.ADMIN)
    m_dev = WorkspaceMember(workspace_id=ws.id, user_id=dev.id, role=WorkspaceRole.DEVELOPER)
    m_viewer = WorkspaceMember(workspace_id=ws.id, user_id=viewer.id, role=WorkspaceRole.VIEWER)
    m_other = WorkspaceMember(workspace_id=ws_other.id, user_id=other_user.id, role=WorkspaceRole.OWNER)
    db_session.add_all([m_owner, m_admin, m_dev, m_viewer, m_other])
    db_session.commit()

    env_staging = Environment(workspace_id=ws.id, name="Staging", key="staging", is_protected=False)
    env_prod = Environment(workspace_id=ws.id, name="Production", key="production", is_protected=True)
    env_other = Environment(workspace_id=ws_other.id, name="Other Env", key="other", is_protected=False)
    db_session.add_all([env_staging, env_prod, env_other])
    db_session.commit()

    srv = Server(
        workspace_id=ws.id,
        environment_id=env_staging.id,
        name="staging-srv",
        ip_address="192.168.1.50",
        ssh_port=22,
        is_active=True,
    )
    srv_prod = Server(
        workspace_id=ws.id,
        environment_id=env_prod.id,
        name="prod-srv",
        ip_address="192.168.1.51",
        ssh_port=22,
        is_active=True,
    )
    db_session.add_all([srv, srv_prod])
    db_session.commit()

    cred = ServerCredential(
        server_id=srv.id,
        auth_type="PASSWORD",
        username="ubuntu",
        encrypted_password=enc.encrypt("secret_pw"),
    )
    cred_prod = ServerCredential(
        server_id=srv_prod.id,
        auth_type="PASSWORD",
        username="ubuntu",
        encrypted_password=enc.encrypt("secret_pw"),
    )
    db_session.add_all([cred, cred_prod])
    db_session.commit()

    return {
        "ws": ws,
        "ws_other": ws_other,
        "owner": owner,
        "admin": admin,
        "dev": dev,
        "viewer": viewer,
        "other_user": other_user,
        "env_staging": env_staging,
        "env_prod": env_prod,
        "env_other": env_other,
        "srv": srv,
        "srv_prod": srv_prod,
    }


def test_backup_config_crud_and_rbac(client: TestClient, setup_backup_env, db_session):
    env = setup_backup_env
    ws_id = env["ws"].id
    srv_id = env["srv"].id
    staging_id = env["env_staging"].id

    owner_token = create_access_token(str(env["owner"].id))
    admin_token = create_access_token(str(env["admin"].id))
    dev_token = create_access_token(str(env["dev"].id))
    viewer_token = create_access_token(str(env["viewer"].id))

    headers_owner = {"Authorization": f"Bearer {owner_token}"}
    headers_admin = {"Authorization": f"Bearer {admin_token}"}
    headers_dev = {"Authorization": f"Bearer {dev_token}"}
    headers_viewer = {"Authorization": f"Bearer {viewer_token}"}

    payload = {
        "name": "Daily Postgres Backup",
        "description": "Daily dump of main DB",
        "environment_id": str(staging_id),
        "server_id": str(srv_id),
        "backup_type": "POSTGRESQL",
        "source": "mydb",
        "destination": "/var/backups/postgresql",
        "retention_days": 14,
        "is_compressed": True,
        "is_active": True,
    }

    # 1. Viewer & Dev cannot create config (403)
    res_v = client.post(f"/api/v1/workspaces/{ws_id}/backup-configs", json=payload, headers=headers_viewer)
    assert res_v.status_code == 403
    res_d = client.post(f"/api/v1/workspaces/{ws_id}/backup-configs", json=payload, headers=headers_dev)
    assert res_d.status_code == 403

    # 2. Admin can create config (201)
    res_a = client.post(f"/api/v1/workspaces/{ws_id}/backup-configs", json=payload, headers=headers_admin)
    assert res_a.status_code == 201
    cfg_data = res_a.json()
    assert cfg_data["name"] == "Daily Postgres Backup"
    assert cfg_data["backup_type"] == "POSTGRESQL"
    config_id = cfg_data["id"]

    # 3. Viewer & Dev can list & read config
    list_res = client.get(f"/api/v1/workspaces/{ws_id}/backup-configs", headers=headers_viewer)
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1

    get_res = client.get(f"/api/v1/workspaces/{ws_id}/backup-configs/{config_id}", headers=headers_dev)
    assert get_res.status_code == 200
    assert get_res.json()["name"] == "Daily Postgres Backup"

    # 4. Owner can update config
    patch_res = client.patch(
        f"/api/v1/workspaces/{ws_id}/backup-configs/{config_id}",
        json={"retention_days": 30, "description": "Updated description"},
        headers=headers_owner,
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["retention_days"] == 30

    # 5. Owner can delete config
    del_res = client.delete(f"/api/v1/workspaces/{ws_id}/backup-configs/{config_id}", headers=headers_owner)
    assert del_res.status_code == 200


def test_backup_config_validation(client: TestClient, setup_backup_env):
    env = setup_backup_env
    ws_id = env["ws"].id
    srv_id = env["srv"].id
    staging_id = env["env_staging"].id
    owner_token = create_access_token(str(env["owner"].id))
    headers_owner = {"Authorization": f"Bearer {owner_token}"}

    # Path traversal rejection
    payload = {
        "name": "Unsafe Backup",
        "environment_id": str(staging_id),
        "server_id": str(srv_id),
        "backup_type": "FILESYSTEM",
        "source": "/opt/app/../etc/shadow",
        "destination": "/var/backups/safe",
    }
    res = client.post(f"/api/v1/workspaces/{ws_id}/backup-configs", json=payload, headers=headers_owner)
    assert res.status_code == 422

    # Relative destination rejection
    payload2 = {
        "name": "Relative Path Backup",
        "environment_id": str(staging_id),
        "server_id": str(srv_id),
        "backup_type": "POSTGRESQL",
        "source": "mydb",
        "destination": "backups/relative",
    }
    res2 = client.post(f"/api/v1/workspaces/{ws_id}/backup-configs", json=payload2, headers=headers_owner)
    assert res2.status_code == 422


def test_backup_trigger_success_and_history(client: TestClient, setup_backup_env, db_session, monkeypatch):
    env = setup_backup_env
    ws_id = env["ws"].id
    srv_id = env["srv"].id
    staging_id = env["env_staging"].id

    owner_token = create_access_token(str(env["owner"].id))
    dev_token = create_access_token(str(env["dev"].id))
    headers_owner = {"Authorization": f"Bearer {owner_token}"}
    headers_dev = {"Authorization": f"Bearer {dev_token}"}

    # Create config
    cfg = BackupConfig(
        workspace_id=ws_id,
        environment_id=staging_id,
        server_id=srv_id,
        name="Test Backup Execution",
        backup_type="POSTGRESQL",
        source="ptbi_db",
        destination="/var/backups/postgresql",
        is_active=True,
    )
    db_session.add(cfg)
    db_session.commit()
    db_session.refresh(cfg)

    # Use mock provider
    mock_prov = MockBackupProvider(succeed=True)
    monkeypatch.setattr(
        "app.api.v1.backups.BackupManagementService",
        lambda db: BackupManagementService(db, provider=mock_prov),
    )

    # Dev cannot trigger backup (403)
    res_dev = client.post(
        f"/api/v1/workspaces/{ws_id}/backup-configs/{cfg.id}/run",
        json={"confirm": True},
        headers=headers_dev,
    )
    assert res_dev.status_code == 403

    # Owner triggers backup (200)
    res = client.post(
        f"/api/v1/workspaces/{ws_id}/backup-configs/{cfg.id}/run",
        json={"confirm": True},
        headers=headers_owner,
    )
    assert res.status_code == 200
    b_data = res.json()
    assert b_data["status"] == "SUCCESS"
    assert b_data["file_name"].startswith("postgresql_ptbi_db")
    assert b_data["checksum"] == mock_prov.checksum
    backup_id = b_data["id"]

    # Check history
    hist_res = client.get(f"/api/v1/workspaces/{ws_id}/backups", headers=headers_owner)
    assert hist_res.status_code == 200
    assert hist_res.json()["total"] >= 1

    # Check logs & secret redaction
    log_res = client.get(f"/api/v1/workspaces/{ws_id}/backups/{backup_id}/logs", headers=headers_owner)
    assert log_res.status_code == 200
    logs_body = log_res.json()
    assert logs_body["lines_returned"] >= 2
    for entry in logs_body["entries"]:
        assert "super_secret_db_pass" not in entry["message"]


def test_backup_verification(client: TestClient, setup_backup_env, db_session, monkeypatch):
    env = setup_backup_env
    ws_id = env["ws"].id
    srv_id = env["srv"].id
    staging_id = env["env_staging"].id
    owner_token = create_access_token(str(env["owner"].id))
    headers_owner = {"Authorization": f"Bearer {owner_token}"}

    cfg = BackupConfig(
        workspace_id=ws_id,
        environment_id=staging_id,
        server_id=srv_id,
        name="Verification Test Config",
        backup_type="FILESYSTEM",
        source="/opt/uploads",
        destination="/var/backups/files",
        is_active=True,
    )
    db_session.add(cfg)
    db_session.commit()

    correct_hash = "11223344556677889900aabbccddeeff11223344556677889900aabbccddeeff"
    backup_row = Backup(
        workspace_id=ws_id,
        environment_id=staging_id,
        server_id=srv_id,
        backup_config_id=cfg.id,
        status="SUCCESS",
        file_name="uploads.tar.gz",
        file_path="/var/backups/files/uploads.tar.gz",
        file_size_bytes=500000,
        checksum=correct_hash,
    )
    db_session.add(backup_row)
    db_session.commit()

    # Successful verification
    mock_prov = MockBackupProvider(succeed=True, checksum=correct_hash)
    monkeypatch.setattr(
        "app.api.v1.backups.BackupManagementService",
        lambda db: BackupManagementService(db, provider=mock_prov),
    )

    verify_res = client.post(
        f"/api/v1/workspaces/{ws_id}/backups/{backup_row.id}/verify",
        json={"confirm": True},
        headers=headers_owner,
    )
    assert verify_res.status_code == 200
    v_data = verify_res.json()
    assert v_data["verified"] is True
    assert v_data["file_exists"] is True


def test_backup_concurrency_lock_409(client: TestClient, setup_backup_env, db_session):
    env = setup_backup_env
    ws_id = env["ws"].id
    srv_id = env["srv"].id
    staging_id = env["env_staging"].id
    owner_token = create_access_token(str(env["owner"].id))
    headers_owner = {"Authorization": f"Bearer {owner_token}"}

    cfg = BackupConfig(
        workspace_id=ws_id,
        environment_id=staging_id,
        server_id=srv_id,
        name="Concurrency Test Config",
        backup_type="DOCKER_VOLUME",
        source="app_volume",
        destination="/var/backups/docker",
        is_active=True,
    )
    db_session.add(cfg)
    db_session.commit()

    # Insert an existing RUNNING backup
    running_backup = Backup(
        workspace_id=ws_id,
        environment_id=staging_id,
        server_id=srv_id,
        backup_config_id=cfg.id,
        status="RUNNING",
    )
    db_session.add(running_backup)
    db_session.commit()

    # Trigger second backup on same config -> must 409
    res = client.post(
        f"/api/v1/workspaces/{ws_id}/backup-configs/{cfg.id}/run",
        json={"confirm": True},
        headers=headers_owner,
    )
    assert res.status_code == 409
    assert "sedang berjalan" in res.json()["detail"].lower()


def test_backup_cross_workspace_isolation(client: TestClient, setup_backup_env):
    env = setup_backup_env
    ws_other_id = env["ws_other"].id
    srv_id = env["srv"].id
    staging_id = env["env_staging"].id
    owner_token = create_access_token(str(env["owner"].id))
    headers_owner = {"Authorization": f"Bearer {owner_token}"}

    payload = {
        "name": "Cross WS Config",
        "environment_id": str(staging_id),
        "server_id": str(srv_id),
        "backup_type": "POSTGRESQL",
        "source": "db",
        "destination": "/var/backups/pg",
    }

    # 1. Non-member accessing other workspace gets 404
    res = client.post(
        f"/api/v1/workspaces/{ws_other_id}/backup-configs",
        json=payload,
        headers=headers_owner,
    )
    assert res.status_code == 404

    # 2. Member trying to reference server from another workspace in own workspace gets 404/400
    payload_cross_server = {
        "name": "Cross Server Config",
        "environment_id": str(staging_id),
        "server_id": str(srv_id),
        "backup_type": "POSTGRESQL",
        "source": "db",
        "destination": "/var/backups/pg",
    }
    # Create server in ws_other
    # referencing environment from ws_other with server from ws1
    payload_cross = {
        "name": "Cross Config",
        "environment_id": str(env["env_other"].id),
        "server_id": str(srv_id),
        "backup_type": "POSTGRESQL",
        "source": "db",
        "destination": "/var/backups/pg",
    }
    res_cross = client.post(
        f"/api/v1/workspaces/{env['ws'].id}/backup-configs",
        json=payload_cross,
        headers=headers_owner,
    )
    assert res_cross.status_code == 404
