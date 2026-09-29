import uuid
from fastapi.testclient import TestClient
from app.core.security import hash_password, create_access_token
from app.models.user import User
from app.models.workspace import Workspace
from app.models.workspace_member import WorkspaceMember, WorkspaceRole
from app.models.environment import Environment
from app.models.server import Server


def create_test_user(db_session, email="term_user@test.com", name="Terminal User", is_active=True):
    user = User(
        email=email,
        name=name,
        password_hash=hash_password("password123"),
        is_active=is_active,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def auth_header(user):
    token = create_access_token(subject=str(user.id))
    return {"Authorization": f"Bearer {token}"}


def test_terminal_status_unauthorized(client: TestClient):
    ws_id = uuid.uuid4()
    server_id = uuid.uuid4()
    response = client.get(f"/api/v1/workspaces/{ws_id}/servers/{server_id}/terminal/status")
    assert response.status_code == 401


def test_terminal_status_authorized(client: TestClient, db_session):
    user = create_test_user(db_session, "operator@test.com", "Operator")
    ws = Workspace(name="Prod Workspace", timezone="Asia/Jakarta")
    db_session.add(ws)
    db_session.commit()

    # Add owner membership
    member = WorkspaceMember(
        workspace_id=ws.id,
        user_id=user.id,
        role=WorkspaceRole.OWNER.value,
    )
    db_session.add(member)

    env = Environment(
        id=uuid.uuid4(),
        workspace_id=ws.id,
        name="Production",
        key="prod",
    )
    db_session.add(env)
    db_session.commit()

    server = Server(
        id=uuid.uuid4(),
        workspace_id=ws.id,
        environment_id=env.id,
        name="Production Shell Host",
        hostname="192.168.1.100",
        ssh_port=22,
        username="root",
        connection_type="SSH",
        is_active=True,
    )
    db_session.add(server)
    db_session.commit()

    response = client.get(
        f"/api/v1/workspaces/{ws.id}/servers/{server.id}/terminal/status",
        headers=auth_header(user),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["server_name"] == "Production Shell Host"
    assert data["port"] == 22
    assert data["user"] == "root"
    assert data["is_active"] is True
