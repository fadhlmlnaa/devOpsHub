import uuid
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.workspace import Workspace
from app.models.workspace_member import WorkspaceMember, WorkspaceRole
from app.models.environment import Environment
from app.models.server import Server
from app.models.agent import Agent, AgentEnrollmentToken, AgentJob
from app.core.security import hash_password, create_access_token
from app.services.agent_manager import AgentManager
from app.services.agent_dispatcher import dispatcher_instance, AgentDispatcher
from app.services.provider_factory import ProviderFactory
from app.infrastructure.service_providers.agent_systemd import AgentSystemdProvider
from app.infrastructure.service_providers.ssh_systemd import SSHSystemdProvider
from agent.dispatcher import AgentLocalDispatcher


@pytest.fixture
def agent_test_setup(db_session: Session):
    owner = User(email="owner_agent@test.com", name="Owner Agent", password_hash=hash_password("Pass123!"))
    developer = User(email="dev_agent@test.com", name="Dev Agent", password_hash=hash_password("Pass123!"))
    viewer = User(email="viewer_agent@test.com", name="Viewer Agent", password_hash=hash_password("Pass123!"))
    db_session.add_all([owner, developer, viewer])
    db_session.commit()

    ws1 = Workspace(name="Workspace Agent 1")
    ws2 = Workspace(name="Workspace Agent 2")
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

    server1 = Server(
        workspace_id=ws1.id,
        environment_id=env1.id,
        name="Agent App Server",
        ip_address="10.0.0.50",
        ssh_port=22,
        connection_type="AGENT",
    )
    server_ssh = Server(
        workspace_id=ws1.id,
        environment_id=env1.id,
        name="SSH App Server",
        ip_address="10.0.0.51",
        ssh_port=22,
        connection_type="SSH",
    )
    db_session.add_all([server1, server_ssh])
    db_session.commit()

    return {
        "owner": owner,
        "dev": developer,
        "viewer": viewer,
        "ws1": ws1,
        "ws2": ws2,
        "env1": env1,
        "server1": server1,
        "server_ssh": server_ssh,
        "owner_token": create_access_token(str(owner.id)),
        "dev_token": create_access_token(str(developer.id)),
        "viewer_token": create_access_token(str(viewer.id)),
    }


def test_agent_enrollment_token_generation_and_rbac(client: TestClient, agent_test_setup, db_session: Session):
    data = agent_test_setup
    ws_id = str(data["ws1"].id)
    server_id = str(data["server1"].id)

    # Developer cannot generate enrollment token
    res = client.post(
        f"/api/v1/workspaces/{ws_id}/servers/{server_id}/agent/enrollment",
        headers={"Authorization": f"Bearer {data['dev_token']}"},
    )
    assert res.status_code == 403

    # Owner can generate enrollment token
    res = client.post(
        f"/api/v1/workspaces/{ws_id}/servers/{server_id}/agent/enrollment",
        headers={"Authorization": f"Bearer {data['owner_token']}"},
        json={"expires_in_minutes": 15},
    )
    assert res.status_code == 200
    resp_data = res.json()
    assert "enrollment_token" in resp_data
    assert "installer_command" in resp_data
    assert resp_data["server_id"] == server_id
    raw_token = resp_data["enrollment_token"]

    # Verify token is hashed in database, not stored plaintext
    db_token = db_session.query(AgentEnrollmentToken).filter_by(server_id=data["server1"].id).first()
    assert db_token is not None
    assert db_token.token_hash != raw_token
    assert db_token.used_at is None


def test_agent_registration_lifecycle(client: TestClient, agent_test_setup, db_session: Session):
    data = agent_test_setup
    ws_id = str(data["ws1"].id)
    server_id = str(data["server1"].id)

    # 1. Generate token
    res = client.post(
        f"/api/v1/workspaces/{ws_id}/servers/{server_id}/agent/enrollment",
        headers={"Authorization": f"Bearer {data['owner_token']}"},
    )
    assert res.status_code == 200
    raw_token = res.json()["enrollment_token"]

    # 2. Register agent via outbound enroll endpoint
    register_payload = {
        "enrollment_token": raw_token,
        "hostname": "test-linux-srv",
        "operating_system": "Ubuntu 22.04 LTS",
        "architecture": "x86_64",
        "agent_version": "1.0.0",
        "capabilities": {"systemd": True, "docker": True, "monitoring": True},
    }
    reg_res = client.post("/api/v1/agent/enroll", json=register_payload)
    assert reg_res.status_code == 200
    reg_data = reg_res.json()
    assert "agent_id" in reg_data
    assert "agent_token" in reg_data
    agent_id = reg_data["agent_id"]
    agent_token = reg_data["agent_token"]

    # 3. Verify single-use token: reused token is rejected
    reused_res = client.post("/api/v1/agent/enroll", json=register_payload)
    assert reused_res.status_code == 400

    # 4. Check Agent status endpoint
    status_res = client.get(
        f"/api/v1/workspaces/{ws_id}/servers/{server_id}/agent",
        headers={"Authorization": f"Bearer {data['dev_token']}"},
    )
    assert status_res.status_code == 200
    agent_status = status_res.json()
    assert agent_status["id"] == agent_id
    assert agent_status["status"] == "ONLINE"
    assert agent_status["capabilities"]["docker"] is True

    # 5. Heartbeat
    hb_res = client.post(
        "/api/v1/agent/heartbeat",
        headers={"X-Agent-Token": agent_token},
        json={
            "agent_id": agent_id,
            "agent_version": "1.0.0",
            "hostname": "test-linux-srv",
            "status": "ONLINE",
            "capabilities": {"systemd": True, "docker": True, "monitoring": True, "custom": True},
        },
    )
    assert hb_res.status_code == 200
    assert hb_res.json()["acknowledged"] is True


def test_agent_enrollment_expired_or_invalid_token(client: TestClient, agent_test_setup, db_session: Session):
    data = agent_test_setup
    ws_id = str(data["ws1"].id)
    server_id = str(data["server1"].id)

    # Create expired token manually
    token_str = "test_expired_token_123"
    token_hash = AgentManager.hash_token(token_str)
    expired_token = AgentEnrollmentToken(
        workspace_id=data["ws1"].id,
        server_id=data["server1"].id,
        token_hash=token_hash,
        expires_at=datetime.now(timezone.utc) - timedelta(minutes=5),
        created_by=data["owner"].id,
    )
    db_session.add(expired_token)
    db_session.commit()

    # Attempt to enroll with expired token
    res = client.post(
        "/api/v1/agent/enroll",
        json={
            "enrollment_token": token_str,
            "hostname": "srv",
            "operating_system": "Linux",
            "architecture": "x86_64",
            "agent_version": "1.0.0",
        },
    )
    assert res.status_code == 400
    assert "kadaluarsa" in res.json()["detail"].lower() or "expired" in res.json()["detail"].lower()


def test_agent_disable_and_revoke(client: TestClient, agent_test_setup, db_session: Session):
    data = agent_test_setup
    ws_id = str(data["ws1"].id)
    server_id = str(data["server1"].id)

    # 1. Generate token and enroll
    res = client.post(
        f"/api/v1/workspaces/{ws_id}/servers/{server_id}/agent/enrollment",
        headers={"Authorization": f"Bearer {data['owner_token']}"},
    )
    token = res.json()["enrollment_token"]
    reg_res = client.post(
        "/api/v1/agent/enroll",
        json={
            "enrollment_token": token,
            "hostname": "srv",
            "operating_system": "Linux",
            "architecture": "x86_64",
            "agent_version": "1.0.0",
        },
    )
    agent_id = reg_res.json()["agent_id"]
    agent_token = reg_res.json()["agent_token"]

    # 2. Disable agent
    dis_res = client.post(
        f"/api/v1/workspaces/{ws_id}/servers/{server_id}/agent/disable",
        headers={"Authorization": f"Bearer {data['owner_token']}"},
    )
    assert dis_res.status_code == 200
    assert dis_res.json()["status"] == "DISABLED"

    # Heartbeat while disabled returns 401
    hb_res = client.post(
        "/api/v1/agent/heartbeat",
        headers={"X-Agent-Token": agent_token},
        json={
            "agent_id": agent_id,
            "agent_version": "1.0.0",
            "hostname": "srv",
            "status": "ONLINE",
        },
    )
    assert hb_res.status_code == 401

    # 3. Revoke agent
    rev_res = client.post(
        f"/api/v1/workspaces/{ws_id}/servers/{server_id}/agent/revoke",
        headers={"Authorization": f"Bearer {data['owner_token']}"},
    )
    assert rev_res.status_code == 200
    assert rev_res.json()["status"] == "DISABLED"
    assert rev_res.json()["is_active"] is False


def test_provider_factory_resolution_and_no_silent_fallback(agent_test_setup, db_session: Session):
    data = agent_test_setup

    # 1. SSH Server resolves to SSH provider
    ssh_srv_provider = ProviderFactory.get_service_provider(data["server_ssh"], db_session)
    assert isinstance(ssh_srv_provider, SSHSystemdProvider)

    # 2. Agent Server resolves to Agent provider
    agent_srv_provider = ProviderFactory.get_service_provider(data["server1"], db_session)
    assert isinstance(agent_srv_provider, AgentSystemdProvider)


def test_agent_local_dispatcher_operation_allowlist_and_security():
    dispatcher = AgentLocalDispatcher()

    # 1. Unknown operation is rejected
    unknown_job = {
        "job_id": str(uuid.uuid4()),
        "operation": "ARBITRARY_SHELL_EXEC",
        "payload": {"cmd": "rm -rf /"},
        "nonce": "n1",
        "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat(),
    }
    res = dispatcher.handle_job(unknown_job)
    assert res["status"] == "FAILED"
    assert "tidak diizinkan" in res["error_message"].lower()

    # 2. Expired job is rejected
    expired_job = {
        "job_id": str(uuid.uuid4()),
        "operation": "GET_SYSTEM_METRICS",
        "payload": {},
        "nonce": "n2",
        "expires_at": (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat(),
    }
    exp_res = dispatcher.handle_job(expired_job)
    assert exp_res["status"] == "FAILED"
    assert exp_res["error_category"] == "EXPIRED_JOB"

    # 3. Duplicate nonce is rejected (replay attack prevention)
    valid_job_1 = {
        "job_id": str(uuid.uuid4()),
        "operation": "GET_SYSTEM_METRICS",
        "payload": {},
        "nonce": "unique_nonce_100",
        "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat(),
    }
    res1 = dispatcher.handle_job(valid_job_1)
    assert res1["status"] == "SUCCESS"
    assert "sections" in res1["result"]
    assert "CPU" in res1["result"]["sections"]

    # Replay same job with same nonce
    res2 = dispatcher.handle_job(valid_job_1)
    assert res2["status"] == "FAILED"
    assert "replay" in res2["error_message"].lower()

    # 4. Command injection protection on service name
    invalid_service_job = {
        "job_id": str(uuid.uuid4()),
        "operation": "GET_SERVICE_STATUS",
        "payload": {"service_name": "nginx; rm -rf /"},
        "nonce": "unique_nonce_101",
        "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat(),
    }
    inj_res = dispatcher.handle_job(invalid_service_job)
    assert inj_res["status"] == "FAILED"
    assert "tidak valid" in inj_res["error_message"].lower()
