from datetime import datetime, timedelta, timezone
import jwt
from app.core.config import settings
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    generate_refresh_token,
    hash_refresh_token,
)
from app.models.user import User
from app.models.refresh_token import RefreshToken


# ==========================================
# 1. REGISTER TESTS
# ==========================================

def test_register_success(client, db_session):
    """Test user registration succeeds, password is saved as hash, and no password returned."""
    payload = {
        "name": "Fadhil Maulana",
        "email": "fadhil@example.com",
        "password": "super-strong-password-123",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()

    assert data["name"] == "Fadhil Maulana"
    assert data["email"] == "fadhil@example.com"
    assert data["is_active"] is True
    assert "password" not in data
    assert "password_hash" not in data

    # Verify in database
    db_user = db_session.query(User).filter(User.email == "fadhil@example.com").first()
    assert db_user is not None
    assert db_user.password_hash != "super-strong-password-123"
    assert verify_password("super-strong-password-123", db_user.password_hash) is True


def test_register_duplicate_email_rejected(client, db_session):
    """Test registering with duplicate email returns 409 Conflict."""
    payload = {
        "name": "Fadhil",
        "email": "duplicate@example.com",
        "password": "password123",
    }
    res1 = client.post("/api/v1/auth/register", json=payload)
    assert res1.status_code == 201

    res2 = client.post("/api/v1/auth/register", json=payload)
    assert res2.status_code == 409
    assert "Email sudah terdaftar" in res2.json()["detail"]


def test_register_email_normalized(client, db_session):
    """Test that email is automatically normalized to lowercase and trimmed."""
    payload = {
        "name": "User Caps",
        "email": "  USER.CAPS@Example.COM  ",
        "password": "password123",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    assert response.json()["email"] == "user.caps@example.com"


def test_register_short_password_rejected(client):
    """Test that password shorter than 8 characters is rejected."""
    payload = {
        "name": "Short Pass",
        "email": "short@example.com",
        "password": "123",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 422


# ==========================================
# 2. LOGIN TESTS
# ==========================================

def test_login_success(client, db_session):
    """Test login with valid credentials returns access and refresh tokens."""
    user = User(
        name="Login User",
        email="login@example.com",
        password_hash=hash_password("valid-password-123"),
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "login@example.com", "password": "valid-password-123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password_rejected(client, db_session):
    """Test login with wrong password returns 401 with generic error message."""
    user = User(
        name="Wrong Pass User",
        email="wrongpass@example.com",
        password_hash=hash_password("correct-password"),
    )
    db_session.add(user)
    db_session.commit()

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "wrongpass@example.com", "password": "incorrect-password"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Email atau password salah."


def test_login_nonexistent_email_rejected_generic(client):
    """Test login with unregistered email returns same generic 401 to prevent enumeration."""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "nonexistent@example.com", "password": "any-password"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Email atau password salah."


def test_login_inactive_user_rejected(client, db_session):
    """Test login with inactive user account returns 403 Forbidden."""
    user = User(
        name="Inactive User",
        email="inactive@example.com",
        password_hash=hash_password("password123"),
        is_active=False,
    )
    db_session.add(user)
    db_session.commit()

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "inactive@example.com", "password": "password123"},
    )
    assert response.status_code == 403


# ==========================================
# 3. JWT & PROTECTED /ME TESTS
# ==========================================

def test_get_me_with_valid_token(client, db_session):
    """Test /auth/me returns current user data when valid access token is provided."""
    user = User(
        name="Me User",
        email="me@example.com",
        password_hash=hash_password("password123"),
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()

    token = create_access_token(subject=str(user.id))
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "me@example.com"
    assert data["name"] == "Me User"
    assert "password_hash" not in data


def test_get_me_without_token_rejected(client):
    """Test /auth/me without token returns 401."""
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_get_me_with_expired_token_rejected(client, db_session):
    """Test expired access token is rejected."""
    user = User(
        name="Expired User",
        email="expired@example.com",
        password_hash=hash_password("password123"),
    )
    db_session.add(user)
    db_session.commit()

    expired_token = create_access_token(
        subject=str(user.id),
        expires_delta=timedelta(seconds=-10),
    )
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert response.status_code == 401


def test_get_me_with_invalid_signature_rejected(client):
    """Test token signed with wrong secret is rejected."""
    fake_token = jwt.encode(
        {"sub": "123", "type": "access", "exp": 9999999999},
        "wrong-secret-key-at-least-32-chars-long!",
        algorithm="HS256",
    )
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {fake_token}"},
    )
    assert response.status_code == 401


def test_get_me_with_wrong_token_type_rejected(client, db_session):
    """Test token with type!='access' is rejected."""
    user = User(
        name="Type User",
        email="type@example.com",
        password_hash=hash_password("password123"),
    )
    db_session.add(user)
    db_session.commit()

    invalid_type_token = jwt.encode(
        {"sub": str(user.id), "type": "refresh", "exp": int((datetime.now(timezone.utc) + timedelta(minutes=5)).timestamp())},
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {invalid_type_token}"},
    )
    assert response.status_code == 401


# ==========================================
# 4. REFRESH TOKEN TESTS
# ==========================================

def test_refresh_token_rotation_success(client, db_session):
    """Test valid refresh token creates new access and refresh token, and revokes old one."""
    user = User(
        name="Refresh User",
        email="refresh@example.com",
        password_hash=hash_password("password123"),
    )
    db_session.add(user)
    db_session.commit()

    # Login to get initial refresh token
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "refresh@example.com", "password": "password123"},
    )
    assert login_res.status_code == 200
    old_refresh_token = login_res.json()["refresh_token"]

    # Refresh
    refresh_res = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": old_refresh_token},
    )
    assert refresh_res.status_code == 200
    new_data = refresh_res.json()
    assert "access_token" in new_data
    assert "refresh_token" in new_data
    new_refresh_token = new_data["refresh_token"]
    assert new_refresh_token != old_refresh_token

    # Attempt to reuse old rotated refresh token -> must fail
    reuse_res = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": old_refresh_token},
    )
    assert reuse_res.status_code == 401


def test_refresh_expired_token_rejected(client, db_session):
    """Test expired refresh token is rejected."""
    user = User(
        name="User",
        email="refreshexp@example.com",
        password_hash=hash_password("password123"),
    )
    db_session.add(user)
    db_session.commit()

    raw_token = generate_refresh_token()
    token_hash = hash_refresh_token(raw_token)
    db_token = RefreshToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=datetime.now(timezone.utc) - timedelta(days=1),
    )
    db_session.add(db_token)
    db_session.commit()

    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": raw_token},
    )
    assert response.status_code == 401


# ==========================================
# 5. LOGOUT TESTS
# ==========================================

def test_logout_revokes_refresh_token(client, db_session):
    """Test logout revokes the refresh token so it cannot be used again."""
    user = User(
        name="Logout User",
        email="logout@example.com",
        password_hash=hash_password("password123"),
    )
    db_session.add(user)
    db_session.commit()

    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "logout@example.com", "password": "password123"},
    )
    refresh_token = login_res.json()["refresh_token"]

    # Logout
    logout_res = client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": refresh_token},
    )
    assert logout_res.status_code == 200
    assert logout_res.json()["message"] == "Logout berhasil."

    # Verify refresh fails
    refresh_res = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refresh_res.status_code == 401
