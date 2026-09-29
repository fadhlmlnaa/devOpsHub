import uuid
from app.core.security import hash_password, create_access_token
from app.models.user import User
from app.models.workspace import Workspace
from app.models.workspace_member import WorkspaceMember, WorkspaceRole


def create_test_user(db_session, email="user@test.com", name="Test User", is_active=True):
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


# ==========================================
# 1. WORKSPACE CREATION & LISTING
# ==========================================

def test_create_workspace_success_and_owner_assigned(client, db_session):
    """Test authenticated user creates workspace and is automatically OWNER."""
    user = create_test_user(db_session, "creator@test.com", "Creator")
    res = client.post(
        "/api/v1/workspaces",
        json={"name": "PT Bintang", "description": "Production", "timezone": "Asia/Jakarta"},
        headers=auth_header(user),
    )
    assert res.status_code == 201
    data = res.json()
    assert data["name"] == "PT Bintang"
    assert data["role"] == WorkspaceRole.OWNER.value
    assert data["timezone"] == "Asia/Jakarta"

    # Verify membership in DB
    ws_id = uuid.UUID(data["id"])
    member = db_session.query(WorkspaceMember).filter(
        WorkspaceMember.workspace_id == ws_id,
        WorkspaceMember.user_id == user.id,
    ).first()
    assert member is not None
    assert member.role == WorkspaceRole.OWNER.value


def test_list_workspaces_isolation(client, db_session):
    """Test user only sees workspaces they belong to."""
    user1 = create_test_user(db_session, "u1@test.com", "User 1")
    user2 = create_test_user(db_session, "u2@test.com", "User 2")

    # User 1 creates WS 1
    client.post("/api/v1/workspaces", json={"name": "WS 1"}, headers=auth_header(user1))
    # User 2 creates WS 2
    client.post("/api/v1/workspaces", json={"name": "WS 2"}, headers=auth_header(user2))

    # User 1 list
    res1 = client.get("/api/v1/workspaces", headers=auth_header(user1))
    assert res1.status_code == 200
    items1 = res1.json()
    assert len(items1) == 1
    assert items1[0]["name"] == "WS 1"

    # User 2 list
    res2 = client.get("/api/v1/workspaces", headers=auth_header(user2))
    assert res2.status_code == 200
    items2 = res2.json()
    assert len(items2) == 1
    assert items2[0]["name"] == "WS 2"


# ==========================================
# 2. WORKSPACE DETAIL & ANTI-IDOR
# ==========================================

def test_get_workspace_detail_member_vs_non_member(client, db_session):
    """Test member can get detail, non-member receives 404 (anti-IDOR)."""
    owner = create_test_user(db_session, "owner@test.com", "Owner")
    stranger = create_test_user(db_session, "stranger@test.com", "Stranger")

    res = client.post("/api/v1/workspaces", json={"name": "Private WS"}, headers=auth_header(owner))
    ws_id = res.json()["id"]

    # Owner gets detail
    res_owner = client.get(f"/api/v1/workspaces/{ws_id}", headers=auth_header(owner))
    assert res_owner.status_code == 200
    assert res_owner.json()["role"] == WorkspaceRole.OWNER.value

    # Stranger tries to access -> 404
    res_stranger = client.get(f"/api/v1/workspaces/{ws_id}", headers=auth_header(stranger))
    assert res_stranger.status_code == 404


def test_update_workspace_permissions(client, db_session):
    """Test OWNER and ADMIN can update workspace, DEVELOPER and VIEWER are denied."""
    owner = create_test_user(db_session, "owner_u@test.com", "Owner")
    admin = create_test_user(db_session, "admin_u@test.com", "Admin")
    dev = create_test_user(db_session, "dev_u@test.com", "Dev")
    viewer = create_test_user(db_session, "viewer_u@test.com", "Viewer")

    # Create WS
    res_ws = client.post("/api/v1/workspaces", json={"name": "Original Name"}, headers=auth_header(owner))
    ws_id = res_ws.json()["id"]

    # Add members
    client.post(f"/api/v1/workspaces/{ws_id}/members", json={"email": "admin_u@test.com", "role": "ADMIN"}, headers=auth_header(owner))
    client.post(f"/api/v1/workspaces/{ws_id}/members", json={"email": "dev_u@test.com", "role": "DEVELOPER"}, headers=auth_header(owner))
    client.post(f"/api/v1/workspaces/{ws_id}/members", json={"email": "viewer_u@test.com", "role": "VIEWER"}, headers=auth_header(owner))

    # 1. OWNER updates -> 200
    res = client.patch(f"/api/v1/workspaces/{ws_id}", json={"name": "Updated by Owner"}, headers=auth_header(owner))
    assert res.status_code == 200
    assert res.json()["name"] == "Updated by Owner"

    # 2. ADMIN updates -> 200
    res = client.patch(f"/api/v1/workspaces/{ws_id}", json={"name": "Updated by Admin"}, headers=auth_header(admin))
    assert res.status_code == 200
    assert res.json()["name"] == "Updated by Admin"

    # 3. DEVELOPER updates -> 403
    res = client.patch(f"/api/v1/workspaces/{ws_id}", json={"name": "Updated by Dev"}, headers=auth_header(dev))
    assert res.status_code == 403

    # 4. VIEWER updates -> 403
    res = client.patch(f"/api/v1/workspaces/{ws_id}", json={"name": "Updated by Viewer"}, headers=auth_header(viewer))
    assert res.status_code == 403


# ==========================================
# 3. MEMBER MANAGEMENT & ROLES
# ==========================================

def test_add_member_roles_and_restrictions(client, db_session):
    """Test rules for adding members by OWNER and ADMIN."""
    owner = create_test_user(db_session, "m_owner@test.com", "Owner")
    admin = create_test_user(db_session, "m_admin@test.com", "Admin")
    dev = create_test_user(db_session, "m_dev@test.com", "Dev")
    viewer = create_test_user(db_session, "m_viewer@test.com", "Viewer")
    inactive = create_test_user(db_session, "inactive_m@test.com", "Inactive", is_active=False)

    res_ws = client.post("/api/v1/workspaces", json={"name": "Member WS"}, headers=auth_header(owner))
    ws_id = res_ws.json()["id"]

    # 1. OWNER adds ADMIN -> 201
    res = client.post(f"/api/v1/workspaces/{ws_id}/members", json={"email": "m_admin@test.com", "role": "ADMIN"}, headers=auth_header(owner))
    assert res.status_code == 201

    # 2. Duplicate membership -> 409
    res = client.post(f"/api/v1/workspaces/{ws_id}/members", json={"email": "m_admin@test.com", "role": "ADMIN"}, headers=auth_header(owner))
    assert res.status_code == 409

    # 3. Inactive user cannot be added -> 404
    res = client.post(f"/api/v1/workspaces/{ws_id}/members", json={"email": "inactive_m@test.com", "role": "VIEWER"}, headers=auth_header(owner))
    assert res.status_code == 404

    # 4. OWNER cannot add OWNER role directly -> 400
    res = client.post(f"/api/v1/workspaces/{ws_id}/members", json={"email": "m_dev@test.com", "role": "OWNER"}, headers=auth_header(owner))
    assert res.status_code == 400

    # 5. ADMIN adds DEVELOPER -> 201
    res = client.post(f"/api/v1/workspaces/{ws_id}/members", json={"email": "m_dev@test.com", "role": "DEVELOPER"}, headers=auth_header(admin))
    assert res.status_code == 201

    # 6. ADMIN adds VIEWER -> 201
    res = client.post(f"/api/v1/workspaces/{ws_id}/members", json={"email": "m_viewer@test.com", "role": "VIEWER"}, headers=auth_header(admin))
    assert res.status_code == 201

    # 7. ADMIN tries to add ADMIN -> 403
    extra_user = create_test_user(db_session, "extra@test.com", "Extra")
    res = client.post(f"/api/v1/workspaces/{ws_id}/members", json={"email": "extra@test.com", "role": "ADMIN"}, headers=auth_header(admin))
    assert res.status_code == 403

    # 8. List members
    res = client.get(f"/api/v1/workspaces/{ws_id}/members", headers=auth_header(dev))
    assert res.status_code == 200
    members = res.json()
    assert len(members) == 4
    emails = {m["email"] for m in members}
    assert emails == {"m_owner@test.com", "m_admin@test.com", "m_dev@test.com", "m_viewer@test.com"}


def test_update_member_role_rules(client, db_session):
    """Test role update permissions and owner protection."""
    owner = create_test_user(db_session, "role_owner@test.com", "Owner")
    admin = create_test_user(db_session, "role_admin@test.com", "Admin")
    dev = create_test_user(db_session, "role_dev@test.com", "Dev")

    res_ws = client.post("/api/v1/workspaces", json={"name": "Role WS"}, headers=auth_header(owner))
    ws_id = res_ws.json()["id"]

    client.post(f"/api/v1/workspaces/{ws_id}/members", json={"email": "role_admin@test.com", "role": "ADMIN"}, headers=auth_header(owner))
    client.post(f"/api/v1/workspaces/{ws_id}/members", json={"email": "role_dev@test.com", "role": "DEVELOPER"}, headers=auth_header(owner))

    # 1. OWNER updates DEVELOPER to VIEWER -> 200
    res = client.patch(f"/api/v1/workspaces/{ws_id}/members/{dev.id}", json={"role": "VIEWER"}, headers=auth_header(owner))
    assert res.status_code == 200
    assert res.json()["role"] == "VIEWER"

    # 2. ADMIN updates VIEWER to DEVELOPER -> 200
    res = client.patch(f"/api/v1/workspaces/{ws_id}/members/{dev.id}", json={"role": "DEVELOPER"}, headers=auth_header(admin))
    assert res.status_code == 200
    assert res.json()["role"] == "DEVELOPER"

    # 3. ADMIN tries to update OWNER -> 400/403
    res = client.patch(f"/api/v1/workspaces/{ws_id}/members/{owner.id}", json={"role": "ADMIN"}, headers=auth_header(admin))
    assert res.status_code in [400, 403]

    # 4. Cannot promote anyone to OWNER -> 400
    res = client.patch(f"/api/v1/workspaces/{ws_id}/members/{dev.id}", json={"role": "OWNER"}, headers=auth_header(owner))
    assert res.status_code in [400, 403]


def test_remove_member_and_self_leave(client, db_session):
    """Test member deletion rules and last owner self-leave protection."""
    owner = create_test_user(db_session, "rem_owner@test.com", "Owner")
    admin = create_test_user(db_session, "rem_admin@test.com", "Admin")
    dev = create_test_user(db_session, "rem_dev@test.com", "Dev")

    res_ws = client.post("/api/v1/workspaces", json={"name": "Remove WS"}, headers=auth_header(owner))
    ws_id = res_ws.json()["id"]

    client.post(f"/api/v1/workspaces/{ws_id}/members", json={"email": "rem_admin@test.com", "role": "ADMIN"}, headers=auth_header(owner))
    client.post(f"/api/v1/workspaces/{ws_id}/members", json={"email": "rem_dev@test.com", "role": "DEVELOPER"}, headers=auth_header(owner))

    # 1. ADMIN cannot remove OWNER -> 400/403
    res = client.delete(f"/api/v1/workspaces/{ws_id}/members/{owner.id}", headers=auth_header(admin))
    assert res.status_code in [400, 403]

    # 2. ADMIN cannot remove ADMIN -> 403
    res = client.delete(f"/api/v1/workspaces/{ws_id}/members/{admin.id}", headers=auth_header(admin))
    assert res.status_code in [400, 403]

    # 3. ADMIN removes DEVELOPER -> 200
    res = client.delete(f"/api/v1/workspaces/{ws_id}/members/{dev.id}", headers=auth_header(admin))
    assert res.status_code == 200

    # 4. Sole OWNER tries to leave -> 400
    res = client.delete(f"/api/v1/workspaces/{ws_id}/members/me", headers=auth_header(owner))
    assert res.status_code == 400
    assert "Owner tunggal" in res.json()["detail"]

    # 5. ADMIN self leaves -> 200
    res = client.delete(f"/api/v1/workspaces/{ws_id}/members/me", headers=auth_header(admin))
    assert res.status_code == 200
    assert res.json()["message"] == "Berhasil keluar dari workspace."
