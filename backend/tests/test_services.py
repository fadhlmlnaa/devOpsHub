import uuid
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.core.deps import get_current_user
from app.core.database import get_db
from app.infrastructure.service_providers.base import (
    ServiceActionResult,
    ServiceInfo,
    ServiceListResult,
    ServiceProvider,
)
from app.main import app
from app.models.environment import Environment
from app.models.server import Server
from app.models.server_credential import ServerCredential
from app.models.user import User
from app.models.workspace import Workspace
from app.models.workspace_member import WorkspaceMember, WorkspaceRole
from app.schemas.service import validate_service_name_format
from app.services.encryption import secret_encryption_service
from app.services.service_management import (
    ServiceManagementService,
    get_service_management_service,
)


class MockServiceProvider(ServiceProvider):
    def __init__(self):
        self.is_supported = True
        self.services_list = [
            ServiceInfo(
                name="nginx.service",
                load_state="loaded",
                active_state="active",
                sub_state="running",
                description="A high performance web server",
                enabled=True,
                main_pid=1234,
                active_enter_timestamp="Mon 2026-09-29 10:00:00 UTC",
            ),
            ServiceInfo(
                name="postgresql.service",
                load_state="loaded",
                active_state="active",
                sub_state="running",
                description="PostgreSQL database server",
                enabled=True,
                main_pid=5678,
            ),
            ServiceInfo(
                name="odoo.service",
                load_state="loaded",
                active_state="failed",
                sub_state="failed",
                description="Odoo ERP Server",
                enabled=False,
                main_pid=None,
            ),
        ]
        self.fail_sudo = False

    async def is_systemd_supported(self, host, port, username, password=None, private_key=None, passphrase=None):
        return self.is_supported

    async def list_services(self, host, port, username, password=None, private_key=None, passphrase=None, state=None, limit=100):
        if not self.is_supported:
            return ServiceListResult(
                systemd_supported=False,
                services=[],
                error_message="Systemd tidak didukung atau tidak aktif pada server ini.",
            )

        filtered = self.services_list
        if state:
            filtered = [s for s in self.services_list if s.active_state == state]

        return ServiceListResult(
            systemd_supported=True,
            services=filtered[:limit],
        )

    async def get_service(self, host, port, username, password=None, private_key=None, passphrase=None, service_name=""):
        for s in self.services_list:
            if s.name == service_name:
                return s
        return None

    async def execute_action(self, host, port, username, password=None, private_key=None, passphrase=None, service_name="", action=""):
        if self.fail_sudo:
            return ServiceActionResult(
                success=False,
                service=service_name,
                action=action,
                message="Operasi service membutuhkan akses passwordless sudo atau root.",
                error="SUDO_PASSWORD_REQUIRED",
            )

        prev = await self.get_service(host, port, username, password, private_key, passphrase, service_name)
        prev_dict = {"active_state": prev.active_state, "sub_state": prev.sub_state} if prev else None

        new_active = "active" if action in ("start", "restart", "reload") else "inactive"
        new_sub = "running" if new_active == "active" else "dead"

        # Update in-memory state
        for idx, s in enumerate(self.services_list):
            if s.name == service_name:
                self.services_list[idx] = ServiceInfo(
                    name=s.name,
                    load_state=s.load_state,
                    active_state=new_active,
                    sub_state=new_sub,
                    description=s.description,
                    enabled=s.enabled,
                    main_pid=9999 if new_active == "active" else None,
                )

        curr_dict = {"active_state": new_active, "sub_state": new_sub}
        return ServiceActionResult(
            success=True,
            service=service_name,
            action=action,
            previous_state=prev_dict,
            current_state=curr_dict,
            message=f"Service {service_name} berhasil di-{action}.",
        )


@pytest.fixture
def mock_service_provider():
    return MockServiceProvider()


@pytest.fixture
def client(db_session, mock_service_provider):
    app.dependency_overrides[get_db] = lambda: db_session
    mock_svc = ServiceManagementService(service_provider=mock_service_provider)
    app.dependency_overrides[get_service_management_service] = lambda: mock_svc

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def test_setup(db_session):
    owner = User(email="owner_svc@example.com", password_hash="pw", name="Owner Svc", is_active=True)
    admin = User(email="admin_svc@example.com", password_hash="pw", name="Admin Svc", is_active=True)
    dev = User(email="dev_svc@example.com", password_hash="pw", name="Dev Svc", is_active=True)
    viewer = User(email="viewer_svc@example.com", password_hash="pw", name="Viewer Svc", is_active=True)
    other_user = User(email="other_svc@example.com", password_hash="pw", name="Other Svc", is_active=True)

    db_session.add_all([owner, admin, dev, viewer, other_user])
    db_session.commit()

    workspace = Workspace(name="WS Services", description="Workspace for services test")
    other_workspace = Workspace(name="WS Other", description="Other workspace")
    db_session.add_all([workspace, other_workspace])
    db_session.commit()

    db_session.add(WorkspaceMember(workspace_id=workspace.id, user_id=owner.id, role=WorkspaceRole.OWNER))
    db_session.add(WorkspaceMember(workspace_id=workspace.id, user_id=admin.id, role=WorkspaceRole.ADMIN))
    db_session.add(WorkspaceMember(workspace_id=workspace.id, user_id=dev.id, role=WorkspaceRole.DEVELOPER))
    db_session.add(WorkspaceMember(workspace_id=workspace.id, user_id=viewer.id, role=WorkspaceRole.VIEWER))
    db_session.add(WorkspaceMember(workspace_id=other_workspace.id, user_id=other_user.id, role=WorkspaceRole.OWNER))
    db_session.commit()

    env = Environment(workspace_id=workspace.id, name="Production", key="production")
    other_env = Environment(workspace_id=other_workspace.id, name="Staging", key="staging")
    db_session.add_all([env, other_env])
    db_session.commit()

    server = Server(
        workspace_id=workspace.id,
        environment_id=env.id,
        name="Prod Web",
        hostname="web.prod.internal",
        ip_address="192.168.1.50",
        ssh_port=22,
        username="ubuntu",
        operating_system="Ubuntu 24.04",
    )
    other_server = Server(
        workspace_id=other_workspace.id,
        environment_id=other_env.id,
        name="Other Server",
        hostname="other.internal",
        ip_address="192.168.1.99",
        ssh_port=22,
        username="ubuntu",
    )
    db_session.add_all([server, other_server])
    db_session.commit()

    cred = ServerCredential(
        server_id=server.id,
        auth_type="PASSWORD",
        username="ubuntu",
        encrypted_password=secret_encryption_service.encrypt("supersecret"),
    )
    db_session.add(cred)
    db_session.commit()

    return {
        "workspace": workspace,
        "other_workspace": other_workspace,
        "server": server,
        "other_server": other_server,
        "owner": owner,
        "admin": admin,
        "dev": dev,
        "viewer": viewer,
        "other_user": other_user,
    }


def test_service_name_validation():
    # Valid names
    assert validate_service_name_format("nginx.service") == "nginx.service"
    assert validate_service_name_format("docker.service") == "docker.service"
    assert validate_service_name_format("postgresql@15-main.service") == "postgresql@15-main.service"
    assert validate_service_name_format("odoo-server.service") == "odoo-server.service"

    # Invalid names
    with pytest.raises(ValueError):
        validate_service_name_format("nginx; reboot")

    with pytest.raises(ValueError):
        validate_service_name_format("nginx && rm -rf /")

    with pytest.raises(ValueError):
        validate_service_name_format("$(whoami).service")

    with pytest.raises(ValueError):
        validate_service_name_format("nginx service")

    with pytest.raises(ValueError):
        validate_service_name_format("../../nginx.service")

    with pytest.raises(ValueError):
        validate_service_name_format("nginx.conf")


def test_list_services_success(client, test_setup):
    ws_id = str(test_setup["workspace"].id)
    srv_id = str(test_setup["server"].id)

    app.dependency_overrides[get_current_user] = lambda: test_setup["viewer"]

    res = client.get(f"/api/v1/workspaces/{ws_id}/servers/{srv_id}/services")
    assert res.status_code == 200
    data = res.json()
    assert data["systemd_supported"] is True
    assert len(data["services"]) == 3
    assert data["services"][0]["name"] == "nginx.service"
    assert data["services"][0]["active_state"] == "active"


def test_list_services_filtered(client, test_setup):
    ws_id = str(test_setup["workspace"].id)
    srv_id = str(test_setup["server"].id)

    app.dependency_overrides[get_current_user] = lambda: test_setup["dev"]

    res = client.get(f"/api/v1/workspaces/{ws_id}/servers/{srv_id}/services?state=failed")
    assert res.status_code == 200
    data = res.json()
    assert len(data["services"]) == 1
    assert data["services"][0]["name"] == "odoo.service"


def test_get_service_detail_success_and_not_found(client, test_setup):
    ws_id = str(test_setup["workspace"].id)
    srv_id = str(test_setup["server"].id)

    app.dependency_overrides[get_current_user] = lambda: test_setup["viewer"]

    res = client.get(f"/api/v1/workspaces/{ws_id}/servers/{srv_id}/services/nginx.service")
    assert res.status_code == 200
    data = res.json()
    assert data["name"] == "nginx.service"
    assert data["main_pid"] == 1234
    assert data["enabled"] is True

    # Nonexistent service
    res404 = client.get(f"/api/v1/workspaces/{ws_id}/servers/{srv_id}/services/nonexistent.service")
    assert res404.status_code == 404


def test_service_mutation_permissions(client, test_setup):
    ws_id = str(test_setup["workspace"].id)
    srv_id = str(test_setup["server"].id)

    # 1. VIEWER cannot restart (403)
    app.dependency_overrides[get_current_user] = lambda: test_setup["viewer"]
    res_viewer = client.post(
        f"/api/v1/workspaces/{ws_id}/servers/{srv_id}/services/nginx.service/restart",
        json={"confirm": True},
    )
    assert res_viewer.status_code == 403

    # 2. DEVELOPER cannot restart (403)
    app.dependency_overrides[get_current_user] = lambda: test_setup["dev"]
    res_dev = client.post(
        f"/api/v1/workspaces/{ws_id}/servers/{srv_id}/services/nginx.service/restart",
        json={"confirm": True},
    )
    assert res_dev.status_code == 403

    # 3. ADMIN can restart (200)
    app.dependency_overrides[get_current_user] = lambda: test_setup["admin"]
    res_admin = client.post(
        f"/api/v1/workspaces/{ws_id}/servers/{srv_id}/services/nginx.service/restart",
        json={"confirm": True},
    )
    assert res_admin.status_code == 200
    assert res_admin.json()["success"] is True
    assert res_admin.json()["action"] == "restart"

    # 4. OWNER can stop and start (200)
    app.dependency_overrides[get_current_user] = lambda: test_setup["owner"]
    res_stop = client.post(
        f"/api/v1/workspaces/{ws_id}/servers/{srv_id}/services/nginx.service/stop",
        json={"confirm": True},
    )
    assert res_stop.status_code == 200
    assert res_stop.json()["action"] == "stop"
    assert res_stop.json()["current_state"]["active_state"] == "inactive"

    res_start = client.post(
        f"/api/v1/workspaces/{ws_id}/servers/{srv_id}/services/nginx.service/start",
        json={"confirm": True},
    )
    assert res_start.status_code == 200
    assert res_start.json()["action"] == "start"
    assert res_start.json()["current_state"]["active_state"] == "active"


def test_service_action_confirmation_guard(client, test_setup):
    ws_id = str(test_setup["workspace"].id)
    srv_id = str(test_setup["server"].id)

    app.dependency_overrides[get_current_user] = lambda: test_setup["owner"]

    # confirm=False rejected
    res = client.post(
        f"/api/v1/workspaces/{ws_id}/servers/{srv_id}/services/nginx.service/restart",
        json={"confirm": False},
    )
    assert res.status_code == 422


def test_cross_workspace_service_access_rejected(client, test_setup):
    ws_id = str(test_setup["workspace"].id)
    other_srv_id = str(test_setup["other_server"].id)

    app.dependency_overrides[get_current_user] = lambda: test_setup["owner"]

    # Try accessing server belonging to other workspace
    res = client.get(f"/api/v1/workspaces/{ws_id}/servers/{other_srv_id}/services")
    assert res.status_code == 404


def test_sudo_password_required_error(client, test_setup, mock_service_provider):
    ws_id = str(test_setup["workspace"].id)
    srv_id = str(test_setup["server"].id)

    mock_service_provider.fail_sudo = True
    app.dependency_overrides[get_current_user] = lambda: test_setup["owner"]

    res = client.post(
        f"/api/v1/workspaces/{ws_id}/servers/{srv_id}/services/nginx.service/restart",
        json={"confirm": True},
    )
    assert res.status_code == 403
    assert "passwordless sudo" in res.json()["detail"]
