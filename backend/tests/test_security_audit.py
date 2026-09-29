import uuid
from datetime import datetime, timezone, timedelta
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.rate_limit import limiter_instance
from app.core.security import hash_password, create_access_token, hash_refresh_token, generate_refresh_token
from app.core.validation import validate_safe_identifier, validate_safe_path
from app.models.audit_log import AuditLog
from app.models.environment import Environment
from app.models.refresh_token import RefreshToken
from app.models.server import Server
from app.models.user import User
from app.models.workspace import Workspace
from app.models.workspace_member import WorkspaceMember, WorkspaceRole
from app.schemas.audit_log import AuditAction, AuditStatus
from app.services.audit_service import AuditService
from app.services.redaction import SecretRedactor


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    """Reset rate limiter counts between tests."""
    limiter_instance.reset()
    yield
    limiter_instance.reset()


def create_test_user_and_workspace(db: Session, role: WorkspaceRole = WorkspaceRole.OWNER):
    user = User(
        name=f"User {uuid.uuid4().hex[:6]}",
        email=f"user_{uuid.uuid4().hex[:6]}@example.com",
        password_hash=hash_password("Password123!"),
        is_active=True,
    )
    db.add(user)
    db.flush()

    workspace = Workspace(
        name=f"Workspace {uuid.uuid4().hex[:6]}",
        description="Test workspace",
    )
    db.add(workspace)
    db.flush()

    member = WorkspaceMember(
        workspace_id=workspace.id,
        user_id=user.id,
        role=role.value if isinstance(role, WorkspaceRole) else role,
    )
    db.add(member)
    db.commit()
    db.refresh(user)
    db.refresh(workspace)
    return user, workspace


# =====================================================================
# 1. AUDIT LOGGING & IMMUTABILITY TESTS
# =====================================================================

def test_audit_service_log_creation_and_redaction(db_session: Session):
    """Verify that AuditService logs correctly and redacts sensitive metadata keys."""
    user, ws = create_test_user_and_workspace(db_session)
    audit = AuditService(db_session)

    metadata = {
        "service": "nginx.service",
        "password": "super_secret_password_123",
        "api_key": "secret-api-key",
        "token": "bearer-token-value",
        "safe_info": "operational details",
    }

    log_entry = audit.log(
        action=AuditAction.SERVICE_RESTARTED,
        resource_type="service",
        status=AuditStatus.SUCCESS,
        workspace_id=ws.id,
        user_id=user.id,
        resource_id="nginx.service",
        metadata=metadata,
    )

    assert log_entry is not None
    assert log_entry.action == "SERVICE_RESTARTED"
    assert log_entry.status == "SUCCESS"
    assert log_entry.meta_data["safe_info"] == "operational details"
    assert log_entry.meta_data["password"] == "********"
    assert log_entry.meta_data["api_key"] == "********"
    assert log_entry.meta_data["token"] == "********"


def test_audit_logs_query_api_owner_admin_allowed(client: TestClient, db_session: Session):
    """OWNER and ADMIN can query audit logs with pagination."""
    owner, ws = create_test_user_and_workspace(db_session, WorkspaceRole.OWNER)
    audit = AuditService(db_session)

    # Insert 3 logs
    for i in range(3):
        audit.log(
            action=AuditAction.SERVER_CONNECTION_TESTED,
            resource_type="server",
            status=AuditStatus.SUCCESS,
            workspace_id=ws.id,
            user_id=owner.id,
            metadata={"attempt": i},
        )

    token = create_access_token(subject=str(owner.id))
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get(f"/api/v1/workspaces/{ws.id}/audit-logs?limit=50&offset=0", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 3
    assert len(data["items"]) == 3
    assert data["items"][0]["action"] == "SERVER_CONNECTION_TESTED"


def test_audit_logs_query_developer_viewer_denied(client: TestClient, db_session: Session):
    """DEVELOPER and VIEWER roles are forbidden from viewing audit logs."""
    dev_user, ws = create_test_user_and_workspace(db_session, WorkspaceRole.DEVELOPER)
    token = create_access_token(subject=str(dev_user.id))
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get(f"/api/v1/workspaces/{ws.id}/audit-logs", headers=headers)
    assert res.status_code == 403


def test_audit_logs_immutability(client: TestClient, db_session: Session):
    """Verify that audit logs cannot be edited or deleted via API endpoints."""
    owner, ws = create_test_user_and_workspace(db_session, WorkspaceRole.OWNER)
    token = create_access_token(subject=str(owner.id))
    headers = {"Authorization": f"Bearer {token}"}
    fake_id = uuid.uuid4()

    res_patch = client.patch(f"/api/v1/workspaces/{ws.id}/audit-logs/{fake_id}", headers=headers, json={})
    assert res_patch.status_code in (404, 405)

    res_delete = client.delete(f"/api/v1/workspaces/{ws.id}/audit-logs/{fake_id}", headers=headers)
    assert res_delete.status_code in (404, 405)


# =====================================================================
# 2. AUTHENTICATION HARDENING & REFRESH TOKEN TESTS
# =====================================================================

def test_login_invalid_credentials_returns_generic_error(client: TestClient, db_session: Session):
    """Invalid credentials return generic error message without leaking user existence."""
    res = client.post("/api/v1/auth/login", json={"email": "nonexistent@example.com", "password": "WrongPassword"})
    assert res.status_code == 401
    assert "Email atau password salah." in res.json()["detail"]


def test_refresh_token_rotation(client: TestClient, db_session: Session):
    """Refresh token rotation invalidates old token and returns new token pair."""
    user = User(
        name="Test Rotator",
        email="rotator@example.com",
        password_hash=hash_password("ValidPassword123!"),
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()

    raw_token = generate_refresh_token()
    token_hash = hash_refresh_token(raw_token)
    db_token = RefreshToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=datetime.now(timezone.utc) + timedelta(days=30),
    )
    db_session.add(db_token)
    db_session.commit()

    res = client.post("/api/v1/auth/refresh", json={"refresh_token": raw_token})
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["refresh_token"] != raw_token

    # Old token must now be revoked
    db_session.refresh(db_token)
    assert db_token.revoked_at is not None


def test_revoked_refresh_token_reuse_detection(client: TestClient, db_session: Session):
    """Attempting to use an already revoked token revokes user session family and denies."""
    user = User(
        name="Test Victim",
        email="victim@example.com",
        password_hash=hash_password("ValidPassword123!"),
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()

    # Create one already-revoked token
    revoked_raw = generate_refresh_token()
    revoked_hash = hash_refresh_token(revoked_raw)
    db_revoked = RefreshToken(
        user_id=user.id,
        token_hash=revoked_hash,
        expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        revoked_at=datetime.now(timezone.utc),
    )

    # Create another active token
    active_raw = generate_refresh_token()
    active_hash = hash_refresh_token(active_raw)
    db_active = RefreshToken(
        user_id=user.id,
        token_hash=active_hash,
        expires_at=datetime.now(timezone.utc) + timedelta(days=30),
    )
    db_session.add_all([db_revoked, db_active])
    db_session.commit()

    # Attack: re-use the revoked token
    res = client.post("/api/v1/auth/refresh", json={"refresh_token": revoked_raw})
    assert res.status_code == 401

    # Verify active token in family was also invalidated
    db_session.refresh(db_active)
    assert db_active.revoked_at is not None


def test_jwt_wrong_type_rejected(client: TestClient, db_session: Session):
    """Tokens with type != 'access' cannot be used as bearer authentication."""
    user, ws = create_test_user_and_workspace(db_session)
    refresh_claim_token = create_access_token(subject=str(user.id), extra_claims={"type": "refresh"})

    res = client.get(f"/api/v1/workspaces/{ws.id}", headers={"Authorization": f"Bearer {refresh_claim_token}"})
    assert res.status_code == 401


# =====================================================================
# 3. RATE LIMITING TESTS
# =====================================================================

def test_rate_limiting_on_login(client: TestClient, monkeypatch):
    """Rate limit trips with 429 when max requests threshold is exceeded."""
    # Set limit to 2 for test
    from app.core import config
    monkeypatch.setattr(config.settings, "AUTH_LOGIN_RATE_LIMIT", 2)
    monkeypatch.setattr(config.settings, "AUTH_RATE_LIMIT_ENABLED", True)

    # First request
    r1 = client.post("/api/v1/auth/login", json={"email": "a@ex.com", "password": "x"})
    assert r1.status_code == 401

    # Second request
    r2 = client.post("/api/v1/auth/login", json={"email": "a@ex.com", "password": "x"})
    assert r2.status_code == 401

    # Third request should trip 429 Too Many Requests
    r3 = client.post("/api/v1/auth/login", json={"email": "a@ex.com", "password": "x"})
    assert r3.status_code == 429
    assert "Retry-After" in r3.headers


# =====================================================================
# 4. SECURITY HEADERS & INPUT VALIDATION TESTS
# =====================================================================

def test_security_headers_present_in_response(client: TestClient):
    """All responses include modern security hardening headers."""
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    assert res.headers.get("X-Content-Type-Options") == "nosniff"
    assert res.headers.get("X-Frame-Options") == "DENY"
    assert res.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"


def test_input_validation_and_path_traversal():
    """Test validation utilities rejecting shell injection and path traversal."""
    # Safe identifiers
    assert validate_safe_identifier("nginx.service") == "nginx.service"
    assert validate_safe_identifier("odoo_web_1") == "odoo_web_1"

    # Injection characters rejected
    with pytest.raises(Exception):
        validate_safe_identifier("nginx; rm -rf /")

    with pytest.raises(Exception):
        validate_safe_identifier("docker\x00inject")

    # Path traversal rejected
    with pytest.raises(Exception):
        validate_safe_path("../../etc/passwd")

    with pytest.raises(Exception):
        validate_safe_path("/etc/shadow")


# =====================================================================
# 5. IDOR & CROSS-WORKSPACE ISOLATION TESTS
# =====================================================================

def test_cross_workspace_idor_isolation(client: TestClient, db_session: Session):
    """User in Workspace A cannot access resources in Workspace B."""
    user_a, ws_a = create_test_user_and_workspace(db_session)
    user_b, ws_b = create_test_user_and_workspace(db_session)

    env_b = Environment(workspace_id=ws_b.id, name="Staging", key="staging")
    db_session.add(env_b)
    db_session.flush()

    server_b = Server(workspace_id=ws_b.id, environment_id=env_b.id, name="Server B", is_active=True)
    db_session.add(server_b)
    db_session.commit()

    token_a = create_access_token(subject=str(user_a.id))
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # User A tries to access Server B in Workspace B
    res = client.get(f"/api/v1/workspaces/{ws_b.id}/servers/{server_b.id}", headers=headers_a)
    assert res.status_code in (403, 404)

    # User A tries to access Workspace B audit logs
    res_audit = client.get(f"/api/v1/workspaces/{ws_b.id}/audit-logs", headers=headers_a)
    assert res_audit.status_code in (403, 404)
