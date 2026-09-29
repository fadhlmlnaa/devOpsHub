import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.workspace import Workspace
from app.models.workspace_member import WorkspaceMember, WorkspaceRole
from app.models.environment import Environment
from app.models.server import Server
from app.core.security import hash_password, create_access_token


@pytest.fixture
def test_users_and_workspaces(db_session: Session):
    owner = User(
        email="owner_env@test.com",
        name="Owner Env",
        password_hash=hash_password("Password123!"),
    )
    viewer = User(
        email="viewer_env@test.com",
        name="Viewer Env",
        password_hash=hash_password("Password123!"),
    )
    other_user = User(
        email="other_env@test.com",
        name="Other Env",
        password_hash=hash_password("Password123!"),
    )
    db_session.add_all([owner, viewer, other_user])
    db_session.commit()

    ws1 = Workspace(name="Workspace 1")
    ws2 = Workspace(name="Workspace 2")
    db_session.add_all([ws1, ws2])
    db_session.commit()

    m_owner = WorkspaceMember(workspace_id=ws1.id, user_id=owner.id, role=WorkspaceRole.OWNER)
    m_viewer = WorkspaceMember(workspace_id=ws1.id, user_id=viewer.id, role=WorkspaceRole.VIEWER)
    m_other = WorkspaceMember(workspace_id=ws2.id, user_id=other_user.id, role=WorkspaceRole.OWNER)
    db_session.add_all([m_owner, m_viewer, m_other])
    db_session.commit()

    return {
        "owner": owner,
        "viewer": viewer,
        "other": other_user,
        "ws1": ws1,
        "ws2": ws2,
        "owner_token": create_access_token(str(owner.id)),
        "viewer_token": create_access_token(str(viewer.id)),
        "other_token": create_access_token(str(other_user.id)),
    }


def test_create_environment_owner(client: TestClient, test_users_and_workspaces):
    data = test_users_and_workspaces
    resp = client.post(
        f"/api/v1/workspaces/{data['ws1'].id}/environments",
        json={"name": "Production", "key": "production", "description": "Prod env"},
        headers={"Authorization": f"Bearer {data['owner_token']}"},
    )
    assert resp.status_code == 201
    res_data = resp.json()
    assert res_data["name"] == "Production"
    assert res_data["key"] == "production"
    assert res_data["server_count"] == 0


def test_create_environment_duplicate_key_rejected(client: TestClient, test_users_and_workspaces):
    data = test_users_and_workspaces
    client.post(
        f"/api/v1/workspaces/{data['ws1'].id}/environments",
        json={"name": "Staging", "key": "staging"},
        headers={"Authorization": f"Bearer {data['owner_token']}"},
    )
    # Attempt duplicate key in same workspace
    resp = client.post(
        f"/api/v1/workspaces/{data['ws1'].id}/environments",
        json={"name": "Staging 2", "key": "staging"},
        headers={"Authorization": f"Bearer {data['owner_token']}"},
    )
    assert resp.status_code == 409
    assert "sudah ada" in resp.json()["detail"]


def test_create_environment_viewer_forbidden(client: TestClient, test_users_and_workspaces):
    data = test_users_and_workspaces
    resp = client.post(
        f"/api/v1/workspaces/{data['ws1'].id}/environments",
        json={"name": "Dev", "key": "dev"},
        headers={"Authorization": f"Bearer {data['viewer_token']}"},
    )
    assert resp.status_code == 403


def test_list_environments_and_isolation(client: TestClient, test_users_and_workspaces):
    data = test_users_and_workspaces
    client.post(
        f"/api/v1/workspaces/{data['ws1'].id}/environments",
        json={"name": "Dev", "key": "dev"},
        headers={"Authorization": f"Bearer {data['owner_token']}"},
    )

    # Viewer in ws1 can list
    resp = client.get(
        f"/api/v1/workspaces/{data['ws1'].id}/environments",
        headers={"Authorization": f"Bearer {data['viewer_token']}"},
    )
    assert resp.status_code == 200
    assert len(resp.json()) >= 1

    # User in ws2 cannot access ws1 environments (anti-IDOR returns 404)
    resp2 = client.get(
        f"/api/v1/workspaces/{data['ws1'].id}/environments",
        headers={"Authorization": f"Bearer {data['other_token']}"},
    )
    assert resp2.status_code == 404

def test_delete_environment_with_servers_protected(client: TestClient, test_users_and_workspaces, db_session: Session):
    data = test_users_and_workspaces
    resp = client.post(
        f"/api/v1/workspaces/{data['ws1'].id}/environments",
        json={"name": "Production Protected", "key": "prod-prot"},
        headers={"Authorization": f"Bearer {data['owner_token']}"},
    )
    env_id = uuid.UUID(resp.json()["id"])

    # Add a server inside this environment
    server = Server(
        workspace_id=data["ws1"].id,
        environment_id=env_id,
        name="Server 1",
        ssh_port=22,
    )
    db_session.add(server)
    db_session.commit()

    # Attempt delete should fail with 409
    del_resp = client.delete(
        f"/api/v1/workspaces/{data['ws1'].id}/environments/{env_id}",
        headers={"Authorization": f"Bearer {data['owner_token']}"},
    )
    assert del_resp.status_code == 409
    assert "masih memiliki server" in del_resp.json()["detail"]

    # Remove server first
    db_session.delete(server)
    db_session.commit()

    # Now delete should succeed
    del_resp2 = client.delete(
        f"/api/v1/workspaces/{data['ws1'].id}/environments/{env_id}",
        headers={"Authorization": f"Bearer {data['owner_token']}"},
    )
    assert del_resp2.status_code == 204
