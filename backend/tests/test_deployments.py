import uuid
from unittest.mock import AsyncMock, patch
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.deployment import DeploymentConfig, Deployment, DeploymentLog
from app.models.environment import Environment
from app.models.server import Server
from app.models.server_credential import ServerCredential
from app.models.user import User
from app.models.workspace import Workspace
from app.models.workspace_member import WorkspaceMember, WorkspaceRole
from app.services.encryption import SecretEncryptionService
from app.infrastructure.deployment_providers.base import DeploymentExecutionResult


@pytest.fixture
def setup_deployment_env(db_session: Session):
    """Sets up a workspace, owner, developer, viewer, environment, and server."""
    enc = SecretEncryptionService()

    # Users
    owner = User(email=f"owner_{uuid.uuid4().hex[:6]}@test.com", password_hash="pw", name="Owner")
    dev = User(email=f"dev_{uuid.uuid4().hex[:6]}@test.com", password_hash="pw", name="Dev")
    viewer = User(email=f"viewer_{uuid.uuid4().hex[:6]}@test.com", password_hash="pw", name="Viewer")
    other_user = User(email=f"other_{uuid.uuid4().hex[:6]}@test.com", password_hash="pw", name="Other")
    db_session.add_all([owner, dev, viewer, other_user])
    db_session.commit()

    # Workspaces
    ws = Workspace(name="Deployment WS", description="Test Workspace")
    ws_other = Workspace(name="Other WS", description="Other Workspace")
    db_session.add_all([ws, ws_other])
    db_session.commit()

    # Memberships
    m_owner = WorkspaceMember(workspace_id=ws.id, user_id=owner.id, role=WorkspaceRole.OWNER)
    m_dev = WorkspaceMember(workspace_id=ws.id, user_id=dev.id, role=WorkspaceRole.DEVELOPER)
    m_viewer = WorkspaceMember(workspace_id=ws.id, user_id=viewer.id, role=WorkspaceRole.VIEWER)
    m_other = WorkspaceMember(workspace_id=ws_other.id, user_id=other_user.id, role=WorkspaceRole.OWNER)
    db_session.add_all([m_owner, m_dev, m_viewer, m_other])
    db_session.commit()

    # Environments
    env_staging = Environment(workspace_id=ws.id, name="Staging", key="staging", is_protected=False)
    env_prod = Environment(workspace_id=ws.id, name="Production", key="production", is_protected=True)
    env_other = Environment(workspace_id=ws_other.id, name="Other Staging", key="staging", is_protected=False)
    db_session.add_all([env_staging, env_prod, env_other])
    db_session.commit()

    # Server
    srv = Server(
        workspace_id=ws.id,
        environment_id=env_staging.id,
        name="Staging Server",
        hostname="staging.example.com",
        ip_address="192.168.1.50",
        ssh_port=22,
    )
    srv_prod = Server(
        workspace_id=ws.id,
        environment_id=env_prod.id,
        name="Production Server",
        hostname="prod.example.com",
        ip_address="192.168.1.100",
        ssh_port=22,
    )
    db_session.add_all([srv, srv_prod])
    db_session.commit()

    cred = ServerCredential(
        server_id=srv.id,
        username="ubuntu",
        encrypted_password=enc.encrypt("secret_pw"),
    )
    cred_prod = ServerCredential(
        server_id=srv_prod.id,
        username="ubuntu",
        encrypted_password=enc.encrypt("secret_pw"),
    )
    db_session.add_all([cred, cred_prod])
    db_session.commit()

    return {
        "ws": ws,
        "ws_other": ws_other,
        "owner": owner,
        "dev": dev,
        "viewer": viewer,
        "other_user": other_user,
        "env_staging": env_staging,
        "env_prod": env_prod,
        "env_other": env_other,
        "srv": srv,
        "srv_prod": srv_prod,
    }


def test_deployment_config_crud(client: TestClient, setup_deployment_env):
    env = setup_deployment_env
    ws_id = env["ws"].id
    srv_id = env["srv"].id
    staging_id = env["env_staging"].id

    from app.core.security import create_access_token

    owner_token = create_access_token(str(env["owner"].id))
    viewer_token = create_access_token(str(env["viewer"].id))

    headers_owner = {"Authorization": f"Bearer {owner_token}"}
    headers_viewer = {"Authorization": f"Bearer {viewer_token}"}

    # 1. Viewer cannot create config (403)
    payload = {
        "name": "Odoo Staging App",
        "description": "Deploy staging odoo",
        "application_name": "odoo",
        "working_directory": "/opt/odoo",
        "deployment_type": "SYSTEMD",
        "branch": "main",
        "environment_id": str(staging_id),
        "server_id": str(srv_id),
        "restart_service_name": "odoo.service",
    }
    r_view = client.post(f"/api/v1/workspaces/{ws_id}/deployment-configs", json=payload, headers=headers_viewer)
    assert r_view.status_code == 403

    # 2. Owner can create config (201)
    r_create = client.post(f"/api/v1/workspaces/{ws_id}/deployment-configs", json=payload, headers=headers_owner)
    assert r_create.status_code == 201
    cfg_data = r_create.json()
    cfg_id = cfg_data["id"]
    assert cfg_data["name"] == "Odoo Staging App"
    assert cfg_data["environment_name"] == "Staging"
    assert cfg_data["server_name"] == "Staging Server"

    # 3. List configs (both viewer and owner can list)
    r_list = client.get(f"/api/v1/workspaces/{ws_id}/deployment-configs", headers=headers_viewer)
    assert r_list.status_code == 200
    assert len(r_list.json()) == 1

    # 4. Get config detail
    r_get = client.get(f"/api/v1/workspaces/{ws_id}/deployment-configs/{cfg_id}", headers=headers_viewer)
    assert r_get.status_code == 200
    assert r_get.json()["id"] == cfg_id

    # 5. Update config (Owner)
    r_update = client.patch(
        f"/api/v1/workspaces/{ws_id}/deployment-configs/{cfg_id}",
        json={"name": "Odoo Staging v2", "branch": "staging"},
        headers=headers_owner,
    )
    assert r_update.status_code == 200
    assert r_update.json()["name"] == "Odoo Staging v2"
    assert r_update.json()["branch"] == "staging"

    # 6. Delete config (Owner)
    r_del = client.delete(f"/api/v1/workspaces/{ws_id}/deployment-configs/{cfg_id}", headers=headers_owner)
    assert r_del.status_code == 200
    assert r_del.json()["success"] is True


def test_deployment_config_validation(client: TestClient, setup_deployment_env):
    env = setup_deployment_env
    ws_id = env["ws"].id
    srv_id = env["srv"].id
    staging_id = env["env_staging"].id

    from app.core.security import create_access_token

    headers = {"Authorization": f"Bearer {create_access_token(str(env['owner'].id))}"}

    # Invalid working directory (relative path or command injection)
    bad_payloads = [
        {"working_directory": "opt/odoo"},
        {"working_directory": "/opt/odoo; rm -rf /"},
        {"working_directory": "/opt/odoo/../etc"},
        {"branch": "main; reboot"},
        {"restart_service_name": "odoo_service"},  # missing .service
        {"health_check_url": "ftp://example.com"},  # not http/https
    ]

    for bad in bad_payloads:
        base = {
            "name": "Test App",
            "application_name": "test",
            "working_directory": "/opt/app",
            "deployment_type": "SYSTEMD",
            "environment_id": str(staging_id),
            "server_id": str(srv_id),
        }
        base.update(bad)
        res = client.post(f"/api/v1/workspaces/{ws_id}/deployment-configs", json=base, headers=headers)
        assert res.status_code == 422


def test_deployment_trigger_success_and_history(client: TestClient, setup_deployment_env):
    env = setup_deployment_env
    ws_id = env["ws"].id
    srv_id = env["srv"].id
    staging_id = env["env_staging"].id

    from app.core.security import create_access_token

    headers_owner = {"Authorization": f"Bearer {create_access_token(str(env['owner'].id))}"}
    headers_viewer = {"Authorization": f"Bearer {create_access_token(str(env['viewer'].id))}"}

    # Create config
    payload = {
        "name": "Node API Staging",
        "application_name": "node-api",
        "working_directory": "/opt/node-api",
        "deployment_type": "SYSTEMD",
        "branch": "main",
        "environment_id": str(staging_id),
        "server_id": str(srv_id),
        "restart_service_name": "node-api.service",
    }
    r_cfg = client.post(f"/api/v1/workspaces/{ws_id}/deployment-configs", json=payload, headers=headers_owner)
    assert r_cfg.status_code == 201
    cfg_id = r_cfg.json()["id"]

    mock_result = DeploymentExecutionResult(
        success=True,
        status="SUCCESS",
        commit_reference="a1b2c3d",
        message="Deployment completed successfully.",
        logs=[
            {"sequence": 1, "timestamp": "2026-09-29T10:00:00Z", "level": "INFO", "message": "Starting deploy"},
            {"sequence": 2, "timestamp": "2026-09-29T10:00:05Z", "level": "INFO", "message": "Git pull success"},
            {"sequence": 3, "timestamp": "2026-09-29T10:00:10Z", "level": "INFO", "message": "Service restarted"},
        ],
    )

    with patch("app.infrastructure.deployment_providers.ssh_deployment.SSHDeploymentProvider.deploy", new_callable=AsyncMock) as mock_deploy:
        mock_deploy.return_value = mock_result

        # Trigger deployment
        r_deploy = client.post(
            f"/api/v1/workspaces/{ws_id}/deployment-configs/{cfg_id}/deploy",
            json={"confirm": True},
            headers=headers_owner,
        )
        assert r_deploy.status_code == 200
        dep_data = r_deploy.json()
        assert dep_data["status"] == "SUCCESS"
        assert dep_data["commit_reference"] == "a1b2c3d"
        dep_id = dep_data["id"]

        # View History
        r_hist = client.get(f"/api/v1/workspaces/{ws_id}/deployments", headers=headers_viewer)
        assert r_hist.status_code == 200
        assert r_hist.json()["total"] == 1
        assert r_hist.json()["items"][0]["id"] == dep_id

        # View Logs
        r_logs = client.get(f"/api/v1/workspaces/{ws_id}/deployments/{dep_id}/logs?lines=50", headers=headers_viewer)
        assert r_logs.status_code == 200
        logs_data = r_logs.json()
        assert logs_data["lines_returned"] == 3
        assert logs_data["entries"][0]["message"] == "Starting deploy"


def test_deployment_protected_environment_and_confirmation(client: TestClient, setup_deployment_env):
    env = setup_deployment_env
    ws_id = env["ws"].id
    prod_srv_id = env["srv_prod"].id
    prod_id = env["env_prod"].id

    from app.core.security import create_access_token

    headers_owner = {"Authorization": f"Bearer {create_access_token(str(env['owner'].id))}"}
    headers_dev = {"Authorization": f"Bearer {create_access_token(str(env['dev'].id))}"}

    # Create Prod config
    payload = {
        "name": "Production App",
        "application_name": "prod-app",
        "working_directory": "/opt/prod-app",
        "deployment_type": "DOCKER_COMPOSE",
        "compose_project_name": "prod_stack",
        "environment_id": str(prod_id),
        "server_id": str(prod_srv_id),
    }
    r_cfg = client.post(f"/api/v1/workspaces/{ws_id}/deployment-configs", json=payload, headers=headers_owner)
    assert r_cfg.status_code == 201
    cfg_id = r_cfg.json()["id"]
    assert r_cfg.json()["environment_is_protected"] is True

    # Developer cannot deploy (403)
    r_dev = client.post(
        f"/api/v1/workspaces/{ws_id}/deployment-configs/{cfg_id}/deploy",
        json={"confirm": True},
        headers=headers_dev,
    )
    assert r_dev.status_code == 403

    # Deploy without confirmation (confirm: false) -> 400
    r_no_conf = client.post(
        f"/api/v1/workspaces/{ws_id}/deployment-configs/{cfg_id}/deploy",
        json={"confirm": False},
        headers=headers_owner,
    )
    assert r_no_conf.status_code == 400


def test_deployment_concurrency_lock_409(client: TestClient, setup_deployment_env, db_session: Session):
    env = setup_deployment_env
    ws_id = env["ws"].id
    srv_id = env["srv"].id
    staging_id = env["env_staging"].id

    from app.core.security import create_access_token

    headers_owner = {"Authorization": f"Bearer {create_access_token(str(env['owner'].id))}"}

    # Create config
    cfg = DeploymentConfig(
        workspace_id=ws_id,
        environment_id=staging_id,
        server_id=srv_id,
        name="Concurrent Test App",
        application_name="concurrent-app",
        working_directory="/opt/app",
        deployment_type="SYSTEMD",
        is_active=True,
    )
    db_session.add(cfg)
    db_session.commit()

    # Simulate an active RUNNING deployment
    running_dep = Deployment(
        workspace_id=ws_id,
        environment_id=staging_id,
        server_id=srv_id,
        deployment_config_id=cfg.id,
        status="RUNNING",
    )
    db_session.add(running_dep)
    db_session.commit()

    # Attempt to trigger another deployment on same config -> 409 Conflict
    r_dup = client.post(
        f"/api/v1/workspaces/{ws_id}/deployment-configs/{cfg.id}/deploy",
        json={"confirm": True},
        headers=headers_owner,
    )
    assert r_dup.status_code == 409
    assert "Deployment sedang berjalan" in r_dup.json()["detail"]


def test_deployment_secret_redaction(client: TestClient, setup_deployment_env):
    env = setup_deployment_env
    ws_id = env["ws"].id
    srv_id = env["srv"].id
    staging_id = env["env_staging"].id

    from app.core.security import create_access_token

    headers_owner = {"Authorization": f"Bearer {create_access_token(str(env['owner'].id))}"}

    payload = {
        "name": "Secret Redaction Test",
        "application_name": "secret-test",
        "working_directory": "/opt/app",
        "deployment_type": "SYSTEMD",
        "environment_id": str(staging_id),
        "server_id": str(srv_id),
    }
    r_cfg = client.post(f"/api/v1/workspaces/{ws_id}/deployment-configs", json=payload, headers=headers_owner)
    assert r_cfg.status_code == 201
    cfg_id = r_cfg.json()["id"]

    mock_result = DeploymentExecutionResult(
        success=True,
        status="SUCCESS",
        commit_reference="deadbeef",
        message="Deployed with secrets",
        logs=[
            {
                "sequence": 1,
                "timestamp": "2026-09-29T10:00:00Z",
                "level": "INFO",
                "message": "Loaded env password=SuperSecretPassword123 with token=ghp_ABC123456789XYZ and Authorization: Bearer secret_jwt_token",
            }
        ],
    )

    with patch("app.infrastructure.deployment_providers.ssh_deployment.SSHDeploymentProvider.deploy", new_callable=AsyncMock) as mock_deploy:
        mock_deploy.return_value = mock_result

        r_deploy = client.post(
            f"/api/v1/workspaces/{ws_id}/deployment-configs/{cfg_id}/deploy",
            json={"confirm": True},
            headers=headers_owner,
        )
        assert r_deploy.status_code == 200
        dep_id = r_deploy.json()["id"]

        r_logs = client.get(f"/api/v1/workspaces/{ws_id}/deployments/{dep_id}/logs", headers=headers_owner)
        assert r_logs.status_code == 200
        log_msg = r_logs.json()["entries"][0]["message"]
        assert "SuperSecretPassword123" not in log_msg
        assert "ghp_ABC123456789XYZ" not in log_msg
        assert "secret_jwt_token" not in log_msg


def test_deployment_cross_workspace_isolation(client: TestClient, setup_deployment_env):
    env = setup_deployment_env
    ws_a_id = env["ws"].id
    ws_b_id = env["ws_other"].id
    srv_a_id = env["srv"].id
    staging_a_id = env["env_staging"].id

    from app.core.security import create_access_token

    headers_owner_a = {"Authorization": f"Bearer {create_access_token(str(env['owner'].id))}"}
    headers_owner_b = {"Authorization": f"Bearer {create_access_token(str(env['other_user'].id))}"}

    # Config in Workspace A
    payload = {
        "name": "WS A App",
        "application_name": "app-a",
        "working_directory": "/opt/app-a",
        "deployment_type": "SYSTEMD",
        "environment_id": str(staging_a_id),
        "server_id": str(srv_a_id),
    }
    r_cfg = client.post(f"/api/v1/workspaces/{ws_a_id}/deployment-configs", json=payload, headers=headers_owner_a)
    assert r_cfg.status_code == 201
    cfg_a_id = r_cfg.json()["id"]

    # User B cannot access WS A configs
    r_get = client.get(f"/api/v1/workspaces/{ws_a_id}/deployment-configs/{cfg_a_id}", headers=headers_owner_b)
    assert r_get.status_code in [403, 404]

    # User B cannot trigger deployment in WS A
    r_dep = client.post(
        f"/api/v1/workspaces/{ws_a_id}/deployment-configs/{cfg_a_id}/deploy",
        json={"confirm": True},
        headers=headers_owner_b,
    )
    assert r_dep.status_code in [403, 404]

