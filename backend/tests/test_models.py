import uuid
import pytest
from sqlalchemy.exc import IntegrityError
from app.models import User, Workspace, WorkspaceMember, WorkspaceRole, Environment, Server


def test_user_creation(db_session):
    """Test that a user can be created with UUID and timestamps."""
    user = User(
        email="test@example.com",
        name="Test User",
        password_hash="hashed_password_123",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    assert isinstance(user.id, uuid.UUID)
    assert user.email == "test@example.com"
    assert user.name == "Test User"
    assert user.is_active is True
    assert user.created_at is not None
    assert user.updated_at is not None


def test_duplicate_user_email_rejected(db_session):
    """Test that duplicate email throws IntegrityError."""
    user1 = User(
        email="duplicate@example.com",
        name="User 1",
        password_hash="hash1",
    )
    user2 = User(
        email="duplicate@example.com",
        name="User 2",
        password_hash="hash2",
    )
    db_session.add(user1)
    db_session.commit()

    db_session.add(user2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_workspace_creation(db_session):
    """Test that a workspace can be created."""
    ws = Workspace(
        name="PTBI",
        description="Core DevOps Workspace",
        timezone="Asia/Jakarta",
    )
    db_session.add(ws)
    db_session.commit()
    db_session.refresh(ws)

    assert isinstance(ws.id, uuid.UUID)
    assert ws.name == "PTBI"
    assert ws.timezone == "Asia/Jakarta"
    assert ws.created_at is not None
    assert ws.updated_at is not None


def test_user_can_belong_to_multiple_workspaces(db_session):
    """Test user multi-workspace membership."""
    user = User(email="fadhil@example.com", name="Fadhil", password_hash="hash")
    ws1 = Workspace(name="PTBI")
    ws2 = Workspace(name="Pangan Makmur")
    db_session.add_all([user, ws1, ws2])
    db_session.commit()

    m1 = WorkspaceMember(workspace_id=ws1.id, user_id=user.id, role=WorkspaceRole.OWNER.value)
    m2 = WorkspaceMember(workspace_id=ws2.id, user_id=user.id, role=WorkspaceRole.DEVELOPER.value)
    db_session.add_all([m1, m2])
    db_session.commit()

    db_session.refresh(user)
    assert len(user.memberships) == 2
    roles = {m.role for m in user.memberships}
    assert roles == {WorkspaceRole.OWNER.value, WorkspaceRole.DEVELOPER.value}


def test_duplicate_workspace_membership_rejected(db_session):
    """Test duplicate user in same workspace is rejected."""
    user = User(email="user@example.com", name="User", password_hash="hash")
    ws = Workspace(name="Single WS")
    db_session.add_all([user, ws])
    db_session.commit()

    m1 = WorkspaceMember(workspace_id=ws.id, user_id=user.id, role=WorkspaceRole.ADMIN.value)
    db_session.add(m1)
    db_session.commit()

    m2 = WorkspaceMember(workspace_id=ws.id, user_id=user.id, role=WorkspaceRole.VIEWER.value)
    db_session.add(m2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_environment_belongs_to_workspace(db_session):
    """Test environment creation and relationship to workspace."""
    ws = Workspace(name="Environment Test WS")
    db_session.add(ws)
    db_session.commit()

    env_dev = Environment(workspace_id=ws.id, name="Development", key="development")
    env_prod = Environment(workspace_id=ws.id, name="Production", key="production")
    db_session.add_all([env_dev, env_prod])
    db_session.commit()

    db_session.refresh(ws)
    assert len(ws.environments) == 2
    keys = {env.key for env in ws.environments}
    assert keys == {"development", "production"}


def test_duplicate_environment_key_in_same_workspace_rejected(db_session):
    """Test duplicate environment key in the same workspace is rejected."""
    ws = Workspace(name="WS Key Test")
    db_session.add(ws)
    db_session.commit()

    env1 = Environment(workspace_id=ws.id, name="Dev 1", key="dev")
    db_session.add(env1)
    db_session.commit()

    env2 = Environment(workspace_id=ws.id, name="Dev 2", key="dev")
    db_session.add(env2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_same_environment_key_in_different_workspaces_allowed(db_session):
    """Test same environment key can exist in different workspaces."""
    ws1 = Workspace(name="WS 1")
    ws2 = Workspace(name="WS 2")
    db_session.add_all([ws1, ws2])
    db_session.commit()

    env1 = Environment(workspace_id=ws1.id, name="Development", key="dev")
    env2 = Environment(workspace_id=ws2.id, name="Development", key="dev")
    db_session.add_all([env1, env2])
    db_session.commit()

    assert env1.id != env2.id
    assert env1.workspace_id != env2.workspace_id


def test_server_belongs_to_workspace_and_environment(db_session):
    """Test server creation with workspace and environment."""
    ws = Workspace(name="Server WS")
    db_session.add(ws)
    db_session.commit()

    env = Environment(workspace_id=ws.id, name="Production", key="prod")
    db_session.add(env)
    db_session.commit()

    server = Server(
        workspace_id=ws.id,
        environment_id=env.id,
        name="Main Web Server",
        hostname="web1.internal",
        ip_address="10.0.0.1",
        ssh_port=22,
        username="deploy",
        operating_system="Ubuntu 22.04",
        is_active=True,
    )
    db_session.add(server)
    db_session.commit()
    db_session.refresh(server)

    assert isinstance(server.id, uuid.UUID)
    assert server.name == "Main Web Server"
    assert server.ssh_port == 22
    assert server.workspace.name == "Server WS"
    assert server.environment.name == "Production"


def test_invalid_workspace_environment_relationship_rejected(db_session):
    """Test validation prevents mismatch between server workspace and environment workspace."""
    ws1 = Workspace(name="Workspace 1")
    ws2 = Workspace(name="Workspace 2")
    db_session.add_all([ws1, ws2])
    db_session.commit()

    env_ws2 = Environment(workspace_id=ws2.id, name="WS2 Staging", key="staging")
    db_session.add(env_ws2)
    db_session.commit()

    # Server assigned to Workspace 1, but environment assigned to Workspace 2
    server = Server(
        workspace_id=ws1.id,
        environment_id=env_ws2.id,
        name="Invalid Server",
    )
    # Testing relationship assignment validation
    with pytest.raises(ValueError) as excinfo:
        server.environment = env_ws2
    assert "does not match server workspace" in str(excinfo.value)


def test_health_check_endpoint(client):
    """Test health check returns status ok and database ok."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data.get("status") == "ok"
