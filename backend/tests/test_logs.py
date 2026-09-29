from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient

from app.core.database import get_db
from app.core.deps import get_current_user
from app.infrastructure.log_providers.base import (
    LogProvider,
    LogQueryResult,
    RawLogEntry,
)
from app.infrastructure.log_providers.ssh_journal import SSHJournalLogProvider
from app.main import app
from app.models.environment import Environment
from app.models.server import Server
from app.models.server_credential import ServerCredential
from app.models.user import User
from app.models.workspace import Workspace
from app.models.workspace_member import WorkspaceMember, WorkspaceRole
from app.services.encryption import secret_encryption_service
from app.services.log_management import (
    LogManagementService,
    get_log_management_service,
)
from app.services.redaction import SecretRedactor, secret_redactor


class MockLogProvider(LogProvider):
    def __init__(self):
        self.systemd_supported = True
        self.fail_timeout = False
        self.fail_ssh = False
        self.entries = [
            RawLogEntry(
                timestamp=datetime(2026, 9, 29, 10, 30, 0, tzinfo=timezone.utc),
                priority="INFO",
                message="Started nginx service.",
            ),
            RawLogEntry(
                timestamp=datetime(2026, 9, 29, 10, 30, 5, tzinfo=timezone.utc),
                priority="WARNING",
                message="Client connection warning: token=secret_token_12345678",
            ),
            RawLogEntry(
                timestamp=datetime(2026, 9, 29, 10, 31, 0, tzinfo=timezone.utc),
                priority="ERROR",
                message="Worker connection failed with password=super_secret_pw",
            ),
        ]

    async def get_service_logs(
        self,
        host,
        port,
        username,
        password=None,
        private_key=None,
        passphrase=None,
        service_name="",
        lines=100,
        since=None,
    ):
        if self.fail_timeout:
            return LogQueryResult(
                service_name=service_name,
                lines_requested=lines,
                lines_returned=0,
                error="TIMEOUT",
            )
        if self.fail_ssh:
            return LogQueryResult(
                service_name=service_name,
                lines_requested=lines,
                lines_returned=0,
                error="SSH_UNAVAILABLE",
            )
        if not self.systemd_supported:
            return LogQueryResult(
                service_name=service_name,
                lines_requested=lines,
                lines_returned=0,
                systemd_supported=False,
                error="SYSTEMD_UNAVAILABLE",
            )

        # Redact messages in entries
        redacted = [
            RawLogEntry(
                timestamp=e.timestamp,
                priority=e.priority,
                message=secret_redactor.redact(e.message),
            )
            for e in self.entries[:lines]
        ]

        return LogQueryResult(
            service_name=service_name,
            lines_requested=lines,
            lines_returned=len(redacted),
            entries=redacted,
        )


@pytest.fixture
def mock_log_provider():
    return MockLogProvider()


@pytest.fixture
def client(db_session, mock_log_provider):
    app.dependency_overrides[get_db] = lambda: db_session
    mock_svc = LogManagementService(log_provider=mock_log_provider)
    app.dependency_overrides[get_log_management_service] = lambda: mock_svc

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def test_setup(db_session):
    owner = User(email="owner_log@example.com", password_hash="pw", name="Owner Log", is_active=True)
    admin = User(email="admin_log@example.com", password_hash="pw", name="Admin Log", is_active=True)
    dev = User(email="dev_log@example.com", password_hash="pw", name="Dev Log", is_active=True)
    viewer = User(email="viewer_log@example.com", password_hash="pw", name="Viewer Log", is_active=True)
    other_user = User(email="other_log@example.com", password_hash="pw", name="Other Log", is_active=True)

    db_session.add_all([owner, admin, dev, viewer, other_user])
    db_session.commit()

    workspace = Workspace(name="WS Logs", description="Workspace for logs test")
    other_workspace = Workspace(name="WS Logs Other", description="Other workspace")
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
        name="Prod Web App",
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


def test_secret_redactor_utility():
    # Passwords & Tokens
    assert SecretRedactor.redact("login password=supersecret123") == "login password=********"
    assert SecretRedactor.redact('{"token": "eyJhbGciOiJIUzI1NiJ9"}') == '{"token": "********"}'
    assert SecretRedactor.redact("Authorization: Bearer eyJhbGciOiJIUzI1NiJ9.test") == "Authorization: Bearer ********"
    assert SecretRedactor.redact("api_key=sk-proj-1234567890abcdef") == "api_key=********"

    # Private key block
    pk = "-----BEGIN RSA PRIVATE KEY-----\nMIIEowIBAAKCAQEA0\n-----END RSA PRIVATE KEY-----"
    assert SecretRedactor.redact(f"Loaded key {pk}") == "Loaded key [REDACTED PRIVATE KEY]"


def test_get_service_logs_all_roles_allowed(client, test_setup):
    ws_id = str(test_setup["workspace"].id)
    srv_id = str(test_setup["server"].id)

    # 1. VIEWER can read logs
    app.dependency_overrides[get_current_user] = lambda: test_setup["viewer"]
    res_viewer = client.get(f"/api/v1/workspaces/{ws_id}/servers/{srv_id}/services/nginx.service/logs")
    assert res_viewer.status_code == 200
    data = res_viewer.json()
    assert data["service"] == "nginx.service"
    assert data["lines_returned"] == 3
    assert "********" in data["entries"][1]["message"]  # token redacted
    assert "********" in data["entries"][2]["message"]  # password redacted

    # 2. DEVELOPER can read logs
    app.dependency_overrides[get_current_user] = lambda: test_setup["dev"]
    res_dev = client.get(f"/api/v1/workspaces/{ws_id}/servers/{srv_id}/services/nginx.service/logs?lines=50&since=10m")
    assert res_dev.status_code == 200
    assert res_dev.json()["since"] == "10m"

    # 3. ADMIN can read logs
    app.dependency_overrides[get_current_user] = lambda: test_setup["admin"]
    res_admin = client.get(f"/api/v1/workspaces/{ws_id}/servers/{srv_id}/services/nginx.service/logs")
    assert res_admin.status_code == 200

    # 4. OWNER can read logs
    app.dependency_overrides[get_current_user] = lambda: test_setup["owner"]
    res_owner = client.get(f"/api/v1/workspaces/{ws_id}/servers/{srv_id}/services/nginx.service/logs")
    assert res_owner.status_code == 200


def test_get_service_logs_validation_and_bounds(client, test_setup):
    ws_id = str(test_setup["workspace"].id)
    srv_id = str(test_setup["server"].id)

    app.dependency_overrides[get_current_user] = lambda: test_setup["owner"]

    # Invalid line bounds (lines < 10 or lines > 1000)
    res_low = client.get(f"/api/v1/workspaces/{ws_id}/servers/{srv_id}/services/nginx.service/logs?lines=5")
    assert res_low.status_code == 422

    res_high = client.get(f"/api/v1/workspaces/{ws_id}/servers/{srv_id}/services/nginx.service/logs?lines=50000")
    assert res_high.status_code == 422

    # Invalid since filter
    res_since = client.get(f"/api/v1/workspaces/{ws_id}/servers/{srv_id}/services/nginx.service/logs?since=invalid_since")
    assert res_since.status_code == 422

    # Invalid service name
    res_name = client.get(f"/api/v1/workspaces/{ws_id}/servers/{srv_id}/services/nginx;rm/logs")
    assert res_name.status_code == 422


def test_cross_workspace_logs_rejected(client, test_setup):
    ws_id = str(test_setup["workspace"].id)
    other_srv_id = str(test_setup["other_server"].id)

    app.dependency_overrides[get_current_user] = lambda: test_setup["owner"]

    res = client.get(f"/api/v1/workspaces/{ws_id}/servers/{other_srv_id}/services/nginx.service/logs")
    assert res.status_code == 404


def test_ssh_journal_parser_and_truncation():
    provider = SSHJournalLogProvider(max_bytes=100)

    # Valid JSON line
    json_line = '{"__REALTIME_TIMESTAMP": "1727603400000000", "PRIORITY": "3", "MESSAGE": "Error connecting to db"}'
    entry = provider._parse_json_line(json_line)
    assert entry.priority == "ERROR"
    assert entry.message == "Error connecting to db"
    assert entry.timestamp is not None

    # Byte array message in JSON
    byte_msg_line = '{"__REALTIME_TIMESTAMP": "1727603400000000", "PRIORITY": "6", "MESSAGE": [79, 107]}'
    byte_entry = provider._parse_json_line(byte_msg_line)
    assert byte_entry.message == "Ok"

    # Malformed non-JSON fallback
    plain_line = "Sep 29 10:30:00 prod-server systemd[1]: Started nginx.service."
    plain_entry = provider._parse_json_line(plain_line)
    assert plain_entry.priority == "UNKNOWN"
    assert plain_entry.message == plain_line
