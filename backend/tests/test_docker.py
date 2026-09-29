import uuid
from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient

from app.core.deps import get_current_user
from app.core.database import get_db
from app.infrastructure.docker_providers.base import (
    ComposeActionResult,
    ComposeServiceStatusResult,
    ComposeStatusResult,
    ContainerActionResult,
    ContainerDetailResult,
    ContainerLogEntryResult,
    ContainerLogsResult,
    ContainerSummaryResult,
    DockerProvider,
    DockerStatusResult,
)
from app.main import app
from app.models.environment import Environment
from app.models.server import Server
from app.models.server_credential import ServerCredential
from app.models.user import User
from app.models.workspace import Workspace
from app.models.workspace_member import WorkspaceMember, WorkspaceRole
from app.api.v1.docker import get_docker_management_service
from app.services.docker_management import DockerManagementService
from app.services.encryption import secret_encryption_service


class MockDockerProvider(DockerProvider):
    def __init__(self):
        self.mock_status = DockerStatusResult(
            installed=True, running=True, version="27.1.1", state="RUNNING"
        )
        self.mock_containers = [
            ContainerSummaryResult(
                id="c123456789ab",
                name="web-nginx",
                image="nginx:alpine",
                status="Up 4 hours",
                state="running",
                created_at="2026-09-29 08:00:00",
                ports=["80:80", "443:443"],
            ),
            ContainerSummaryResult(
                id="d987654321fe",
                name="db-postgres",
                image="postgres:15",
                status="Exited (0) 2 hours ago",
                state="exited",
                created_at="2026-09-29 07:00:00",
                ports=["5432:5432"],
            ),
        ]
        self.mock_detail = ContainerDetailResult(
            id="c123456789ab",
            name="web-nginx",
            image="nginx:alpine",
            state="running",
            status="Up 4 hours",
            created_at="2026-09-29T08:00:00Z",
            started_at="2026-09-29T08:00:01Z",
            ports=["80:80", "443:443"],
            restart_policy="unless-stopped",
            cpu_usage="0.12%",
            memory_usage="15.4MiB / 3.82GiB",
        )
        self.mock_logs = ContainerLogsResult(
            container="web-nginx",
            lines_requested=100,
            lines_returned=2,
            entries=[
                ContainerLogEntryResult(
                    timestamp=datetime.now(timezone.utc),
                    message="Configuration loaded successfully. password=********",
                ),
                ContainerLogEntryResult(
                    timestamp=datetime.now(timezone.utc),
                    message="Listening on 0.0.0.0:80",
                ),
            ],
        )
        self.mock_compose_status = ComposeStatusResult(
            project_name="myapp",
            status="RUNNING",
            services=[
                ComposeServiceStatusResult(name="myapp-web-1", service="web", state="running", status="Up 2 hours"),
                ComposeServiceStatusResult(name="myapp-db-1", service="db", state="running", status="Up 2 hours"),
            ],
        )

    async def get_docker_status(self, host, port, username, password=None, private_key=None, passphrase=None):
        return self.mock_status

    async def list_containers(self, host, port, username, password=None, private_key=None, passphrase=None, state_filter="running"):
        if state_filter == "running":
            return [c for c in self.mock_containers if c.state == "running"]
        elif state_filter == "stopped":
            return [c for c in self.mock_containers if c.state != "running"]
        return self.mock_containers

    async def get_container_detail(self, host, port, username, password=None, private_key=None, passphrase=None, container_id=""):
        if container_id in ["c123456789ab", "web-nginx"]:
            return self.mock_detail
        return None

    async def execute_container_action(self, host, port, username, password=None, private_key=None, passphrase=None, container_id="", action="restart"):
        return ContainerActionResult(
            success=True,
            container=container_id,
            action=action,
            current_state="running" if action in ["start", "restart"] else "exited",
            message=f"Container {container_id} berhasil di-{action}.",
        )

    async def get_container_logs(self, host, port, username, password=None, private_key=None, passphrase=None, container_id="", lines=100, since=None):
        return self.mock_logs

    async def get_compose_status(self, host, port, username, password=None, private_key=None, passphrase=None, working_directory="", compose_file="docker-compose.yml", project_name=""):
        return self.mock_compose_status

    async def execute_compose_action(self, host, port, username, password=None, private_key=None, passphrase=None, working_directory="", compose_file="docker-compose.yml", project_name="", action="restart"):
        return ComposeActionResult(
            success=True,
            project_name=project_name,
            action=action,
            status="RUNNING" if action in ["up", "restart"] else "STOPPED",
            message=f"Docker Compose '{project_name}' berhasil di-{action}.",
        )


@pytest.fixture
def mock_docker_provider():
    return MockDockerProvider()


@pytest.fixture
def client(db_session, mock_docker_provider):
    app.dependency_overrides[get_db] = lambda: db_session
    mock_svc = DockerManagementService(docker_provider=mock_docker_provider)
    app.dependency_overrides[get_docker_management_service] = lambda: mock_svc

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def setup_docker_test_data(db_session):
    owner = User(email="owner_docker@example.com", password_hash="pw", name="Owner Docker", is_active=True)
    admin = User(email="admin_docker@example.com", password_hash="pw", name="Admin Docker", is_active=True)
    dev = User(email="dev_docker@example.com", password_hash="pw", name="Dev Docker", is_active=True)
    viewer = User(email="viewer_docker@example.com", password_hash="pw", name="Viewer Docker", is_active=True)
    other_user = User(email="other_docker@example.com", password_hash="pw", name="Other Docker", is_active=True)

    db_session.add_all([owner, admin, dev, viewer, other_user])
    db_session.commit()

    ws_a = Workspace(name="Docker Workspace A", description="Workspace A")
    ws_b = Workspace(name="Docker Workspace B", description="Workspace B")
    db_session.add_all([ws_a, ws_b])
    db_session.commit()

    db_session.add(WorkspaceMember(workspace_id=ws_a.id, user_id=owner.id, role=WorkspaceRole.OWNER))
    db_session.add(WorkspaceMember(workspace_id=ws_a.id, user_id=admin.id, role=WorkspaceRole.ADMIN))
    db_session.add(WorkspaceMember(workspace_id=ws_a.id, user_id=dev.id, role=WorkspaceRole.DEVELOPER))
    db_session.add(WorkspaceMember(workspace_id=ws_a.id, user_id=viewer.id, role=WorkspaceRole.VIEWER))
    db_session.add(WorkspaceMember(workspace_id=ws_b.id, user_id=other_user.id, role=WorkspaceRole.OWNER))
    db_session.commit()

    env_a = Environment(workspace_id=ws_a.id, name="Production", key="production")
    env_b = Environment(workspace_id=ws_b.id, name="Staging", key="staging")
    db_session.add_all([env_a, env_b])
    db_session.commit()

    server_a = Server(
        workspace_id=ws_a.id,
        environment_id=env_a.id,
        name="Prod-Docker-01",
        hostname="docker01.internal",
        ip_address="192.168.10.100",
        ssh_port=22,
        username="ubuntu",
    )
    server_b = Server(
        workspace_id=ws_b.id,
        environment_id=env_b.id,
        name="Staging-Docker-02",
        hostname="docker02.internal",
        ip_address="192.168.20.100",
        ssh_port=22,
        username="ubuntu",
    )
    db_session.add_all([server_a, server_b])
    db_session.commit()

    cred = ServerCredential(
        server_id=server_a.id,
        auth_type="PASSWORD",
        username="ubuntu",
        encrypted_password=secret_encryption_service.encrypt("test_ssh_password"),
    )
    db_session.add(cred)
    db_session.commit()

    return {
        "ws_a": ws_a,
        "ws_b": ws_b,
        "env_a": env_a,
        "server_a": server_a,
        "server_b": server_b,
        "owner": owner,
        "admin": admin,
        "dev": dev,
        "viewer": viewer,
        "other_user": other_user,
    }


def test_docker_status_detection(client: TestClient, setup_docker_test_data):
    data = setup_docker_test_data
    app.dependency_overrides[get_current_user] = lambda: data["owner"]

    url = f"/api/v1/workspaces/{data['ws_a'].id}/servers/{data['server_a'].id}/docker"
    res = client.get(url)
    assert res.status_code == 200
    payload = res.json()
    assert payload["installed"] is True
    assert payload["running"] is True
    assert payload["version"] == "27.1.1"
    assert payload["state"] == "RUNNING"


def test_list_containers_and_filtering(client: TestClient, setup_docker_test_data):
    data = setup_docker_test_data
    app.dependency_overrides[get_current_user] = lambda: data["viewer"]

    # Default running
    url = f"/api/v1/workspaces/{data['ws_a'].id}/servers/{data['server_a'].id}/docker/containers"
    res = client.get(url)
    assert res.status_code == 200
    payload = res.json()
    assert len(payload["containers"]) == 1
    assert payload["containers"][0]["name"] == "web-nginx"

    # State all
    res_all = client.get(f"{url}?state=all")
    assert res_all.status_code == 200
    assert len(res_all.json()["containers"]) == 2


def test_container_detail_and_validation(client: TestClient, setup_docker_test_data):
    data = setup_docker_test_data
    app.dependency_overrides[get_current_user] = lambda: data["viewer"]

    # Valid container detail
    url = f"/api/v1/workspaces/{data['ws_a'].id}/servers/{data['server_a'].id}/docker/containers/c123456789ab"
    res = client.get(url)
    assert res.status_code == 200
    detail = res.json()
    assert detail["name"] == "web-nginx"
    assert detail["state"] == "running"
    assert detail["restart_policy"] == "unless-stopped"
    assert detail["cpu_usage"] == "0.12%"

    # Invalid container ID rejection (injection test)
    bad_url = f"/api/v1/workspaces/{data['ws_a'].id}/servers/{data['server_a'].id}/docker/containers/nginx;rm"
    bad_res = client.get(bad_url)
    assert bad_res.status_code == 422


def test_container_actions_and_permissions(client: TestClient, setup_docker_test_data):
    data = setup_docker_test_data
    restart_url = f"/api/v1/workspaces/{data['ws_a'].id}/servers/{data['server_a'].id}/docker/containers/web-nginx/restart"

    # 1. Owner can restart container with confirm=True
    app.dependency_overrides[get_current_user] = lambda: data["owner"]

    # Missing confirmation fails
    fail_res = client.post(restart_url, json={"confirm": False})
    assert fail_res.status_code == 400

    # With confirm=True succeeds
    ok_res = client.post(restart_url, json={"confirm": True})
    assert ok_res.status_code == 200
    assert ok_res.json()["success"] is True
    assert ok_res.json()["current_state"] == "running"

    # 2. Admin can restart container with confirm=True
    app.dependency_overrides[get_current_user] = lambda: data["admin"]
    admin_res = client.post(restart_url, json={"confirm": True})
    assert admin_res.status_code == 200

    # 3. Developer cannot mutate container (Read-only on Step 10)
    app.dependency_overrides[get_current_user] = lambda: data["dev"]
    dev_res = client.post(restart_url, json={"confirm": True})
    assert dev_res.status_code == 403

    # 4. Viewer cannot mutate container
    app.dependency_overrides[get_current_user] = lambda: data["viewer"]
    viewer_res = client.post(restart_url, json={"confirm": True})
    assert viewer_res.status_code == 403


def test_container_logs_and_redaction(client: TestClient, setup_docker_test_data):
    data = setup_docker_test_data
    app.dependency_overrides[get_current_user] = lambda: data["viewer"]

    logs_url = f"/api/v1/workspaces/{data['ws_a'].id}/servers/{data['server_a'].id}/docker/containers/web-nginx/logs?lines=50"
    res = client.get(logs_url)
    assert res.status_code == 200
    payload = res.json()
    assert payload["container"] == "web-nginx"
    assert len(payload["entries"]) == 2
    assert "password=********" in payload["entries"][0]["message"]


def test_docker_compose_crud_and_operations(client: TestClient, setup_docker_test_data):
    data = setup_docker_test_data
    compose_base_url = f"/api/v1/workspaces/{data['ws_a'].id}/servers/{data['server_a'].id}/docker/compose/projects"

    # 1. Create Compose Project as Owner
    app.dependency_overrides[get_current_user] = lambda: data["owner"]
    create_payload = {
        "environment_id": str(data["env_a"].id),
        "name": "PTBI Web App",
        "project_name": "ptbi",
        "working_directory": "/opt/apps/ptbi",
        "compose_file": "docker-compose.yml",
        "description": "Main ERP System",
        "is_active": True,
    }
    create_res = client.post(compose_base_url, json=create_payload)
    assert create_res.status_code == 201
    project_data = create_res.json()
    project_id = project_data["id"]
    assert project_data["project_name"] == "ptbi"

    # 2. List Compose Projects as Viewer (Read-only allowed)
    app.dependency_overrides[get_current_user] = lambda: data["viewer"]
    list_res = client.get(compose_base_url)
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1

    # 3. Get Compose Status
    status_url = f"{compose_base_url}/{project_id}/status"
    status_res = client.get(status_url)
    assert status_res.status_code == 200
    assert status_res.json()["status"] == "RUNNING"
    assert len(status_res.json()["services"]) == 2

    # 4. Compose Restart as Developer -> Forbidden (403)
    app.dependency_overrides[get_current_user] = lambda: data["dev"]
    restart_url = f"{compose_base_url}/{project_id}/restart"
    dev_op_res = client.post(restart_url, json={"confirm": True})
    assert dev_op_res.status_code == 403

    # 5. Compose Restart as Admin -> Allowed (200)
    app.dependency_overrides[get_current_user] = lambda: data["admin"]
    admin_op_res = client.post(restart_url, json={"confirm": True})
    assert admin_op_res.status_code == 200
    assert admin_op_res.json()["success"] is True

    # 6. Update Project
    update_url = f"{compose_base_url}/{project_id}"
    up_res = client.patch(update_url, json={"description": "Updated ERP"})
    assert up_res.status_code == 200
    assert up_res.json()["description"] == "Updated ERP"

    # 7. Delete Project
    del_res = client.delete(update_url)
    assert del_res.status_code == 204


def test_docker_cross_workspace_isolation(client: TestClient, setup_docker_test_data):
    data = setup_docker_test_data
    app.dependency_overrides[get_current_user] = lambda: data["dev"]

    # User is member of Workspace A, trying to access Server B in Workspace B -> 403/404 Forbidden
    cross_url = f"/api/v1/workspaces/{data['ws_b'].id}/servers/{data['server_b'].id}/docker"
    res = client.get(cross_url)
    assert res.status_code in [403, 404]
