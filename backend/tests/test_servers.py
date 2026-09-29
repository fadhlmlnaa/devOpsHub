import uuid
import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.workspace import Workspace
from app.models.workspace_member import WorkspaceMember, WorkspaceRole
from app.models.environment import Environment
from app.models.server import Server
from app.models.server_credential import ServerCredential
from app.core.security import hash_password, create_access_token
from app.services.encryption import secret_encryption_service
from app.services.connection_provider import ConnectionResult


@pytest.fixture
def server_test_setup(db_session: Session):
    owner = User(email="owner_srv@test.com", name="Owner Srv", password_hash=hash_password("Pass123!"))
    developer = User(email="dev_srv@test.com", name="Dev Srv", password_hash=hash_password("Pass123!"))
    viewer = User(email="viewer_srv@test.com", name="Viewer Srv", password_hash=hash_password("Pass123!"))
    db_session.add_all([owner, developer, viewer])
    db_session.commit()

    ws1 = Workspace(name="Workspace Srv 1")
    ws2 = Workspace(name="Workspace Srv 2")
    db_session.add_all([ws1, ws2])
    db_session.commit()

    db_session.add_all([
        WorkspaceMember(workspace_id=ws1.id, user_id=owner.id, role=WorkspaceRole.OWNER),
        WorkspaceMember(workspace_id=ws1.id, user_id=developer.id, role=WorkspaceRole.DEVELOPER),
        WorkspaceMember(workspace_id=ws1.id, user_id=viewer.id, role=WorkspaceRole.VIEWER),
    ])
    db_session.commit()

    env1 = Environment(workspace_id=ws1.id, name="Production", key="production")
    env2 = Environment(workspace_id=ws2.id, name="Other Prod", key="other-prod")
    db_session.add_all([env1, env2])
    db_session.commit()

    return {
        "owner": owner,
        "dev": developer,
        "viewer": viewer,
        "ws1": ws1,
        "ws2": ws2,
        "env1": env1,
        "env2": env2,
        "owner_token": create_access_token(str(owner.id)),
        "dev_token": create_access_token(str(developer.id)),
        "viewer_token": create_access_token(str(viewer.id)),
    }


def test_create_server_with_encrypted_credentials(client: TestClient, server_test_setup, db_session: Session):
    data = server_test_setup
    payload = {
        "environment_id": str(data["env1"].id),
        "name": "Production App Server",
        "hostname": "app.prod.internal",
        "ip_address": "103.12.34.56",
        "ssh_port": 2222,
        "username": "ubuntu",
        "operating_system": "Ubuntu 24.04",
        "credential": {
            "auth_type": "PASSWORD",
            "username": "ubuntu",
            "password": "SuperSecretSSHPassword!",
        },
    }

    resp = client.post(
        f"/api/v1/workspaces/{data['ws1'].id}/servers",
        json=payload,
        headers={"Authorization": f"Bearer {data['owner_token']}"},
    )
    assert resp.status_code == 201
    res = resp.json()
    assert res["name"] == "Production App Server"
    assert res["ssh_port"] == 2222
    assert res["has_credential"] is True
    assert res["auth_type"] == "PASSWORD"

    # SECURITY CHECK: Password must NEVER be in response
    assert "password" not in res
    assert "credential" not in res
    assert "SuperSecretSSHPassword!" not in str(res)

    # Database check: credential must be encrypted at rest
    server_id = uuid.UUID(res["id"])
    cred = db_session.query(ServerCredential).filter(ServerCredential.server_id == server_id).first()
    assert cred is not None
    assert cred.encrypted_password is not None
    assert cred.encrypted_password != "SuperSecretSSHPassword!"
    # Decryption check
    assert secret_encryption_service.decrypt(cred.encrypted_password) == "SuperSecretSSHPassword!"


def test_cross_workspace_environment_rejected(client: TestClient, server_test_setup):
    data = server_test_setup
    # Attempt to create server in ws1 using env2 from ws2
    payload = {
        "environment_id": str(data["env2"].id),
        "name": "Cross Server",
        "ssh_port": 22,
    }
    resp = client.post(
        f"/api/v1/workspaces/{data['ws1'].id}/servers",
        json=payload,
        headers={"Authorization": f"Bearer {data['owner_token']}"},
    )
    assert resp.status_code == 400
    assert "Environment tidak valid" in resp.json()["detail"]


def test_server_crud_and_permissions(client: TestClient, server_test_setup):
    data = server_test_setup
    # Create server
    create_resp = client.post(
        f"/api/v1/workspaces/{data['ws1'].id}/servers",
        json={
            "environment_id": str(data["env1"].id),
            "name": "Nginx Proxy",
            "ip_address": "103.10.10.10",
        },
        headers={"Authorization": f"Bearer {data['owner_token']}"},
    )
    assert create_resp.status_code == 201
    srv_id = create_resp.json()["id"]

    # Viewer can read server
    get_resp = client.get(
        f"/api/v1/workspaces/{data['ws1'].id}/servers/{srv_id}",
        headers={"Authorization": f"Bearer {data['viewer_token']}"},
    )
    assert get_resp.status_code == 200
    assert get_resp.json()["name"] == "Nginx Proxy"

    # Viewer cannot update
    patch_resp = client.patch(
        f"/api/v1/workspaces/{data['ws1'].id}/servers/{srv_id}",
        json={"name": "Nginx Updated"},
        headers={"Authorization": f"Bearer {data['viewer_token']}"},
    )
    assert patch_resp.status_code == 403

    # Owner can update
    patch_resp2 = client.patch(
        f"/api/v1/workspaces/{data['ws1'].id}/servers/{srv_id}",
        json={"name": "Nginx Updated"},
        headers={"Authorization": f"Bearer {data['owner_token']}"},
    )
    assert patch_resp2.status_code == 200
    assert patch_resp2.json()["name"] == "Nginx Updated"

    # Owner can delete
    del_resp = client.delete(
        f"/api/v1/workspaces/{data['ws1'].id}/servers/{srv_id}",
        headers={"Authorization": f"Bearer {data['owner_token']}"},
    )
    assert del_resp.status_code == 204


@pytest.mark.asyncio
async def test_ssh_connection_test_success_and_failures(client: TestClient, server_test_setup):
    data = server_test_setup
    # Create server with credential
    create_resp = client.post(
        f"/api/v1/workspaces/{data['ws1'].id}/servers",
        json={
            "environment_id": str(data["env1"].id),
            "name": "Odoo Prod",
            "ip_address": "103.20.20.20",
            "credential": {
                "auth_type": "PASSWORD",
                "username": "root",
                "password": "MySecretPassword123!",
            },
        },
        headers={"Authorization": f"Bearer {data['owner_token']}"},
    )
    srv_id = create_resp.json()["id"]

    # 1. Test Success Mock
    mock_success_result = ConnectionResult(
        success=True,
        message="Koneksi SSH berhasil dan remote command berjalan normal.",
        status="ONLINE",
        server_info={"hostname": "odoo-prod", "operating_system": "Ubuntu 24.04 LTS"},
    )
    with patch("app.api.v1.servers.get_connection_provider") as mock_provider_factory:
        mock_provider = AsyncMock()
        mock_provider.test_connection.return_value = mock_success_result
        mock_provider_factory.return_value = mock_provider

        test_resp = client.post(
            f"/api/v1/workspaces/{data['ws1'].id}/servers/{srv_id}/connection-test",
            headers={"Authorization": f"Bearer {data['dev_token']}"},
        )
        assert test_resp.status_code == 200
        res_body = test_resp.json()
        assert res_body["success"] is True
        assert res_body["status"] == "ONLINE"
        assert res_body["server_info"]["hostname"] == "odoo-prod"

    # 2. Test Failure Mock (Auth failure)
    mock_fail_result = ConnectionResult(
        success=False,
        message="Autentikasi SSH gagal. Periksa kembali username, password, atau private key.",
        status="OFFLINE",
    )
    with patch("app.api.v1.servers.get_connection_provider") as mock_provider_factory:
        mock_provider = AsyncMock()
        mock_provider.test_connection.return_value = mock_fail_result
        mock_provider_factory.return_value = mock_provider

        test_resp2 = client.post(
            f"/api/v1/workspaces/{data['ws1'].id}/servers/{srv_id}/connection-test",
            headers={"Authorization": f"Bearer {data['dev_token']}"},
        )
        assert test_resp2.status_code == 200
        res_body2 = test_resp2.json()
        assert res_body2["success"] is False
        assert res_body2["status"] == "OFFLINE"
        assert "Autentikasi SSH gagal" in res_body2["message"]
