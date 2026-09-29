from datetime import datetime, timedelta, timezone
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.core.rate_limit import rate_limit
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    generate_refresh_token,
    hash_refresh_token,
)
from app.models.user import User
from app.models.refresh_token import RefreshToken
from app.schemas.audit_log import AuditAction, AuditStatus
from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    RefreshTokenRequest,
    LogoutRequest,
    UserMeResponse,
    MessageResponse,
)
from app.services.audit_service import AuditService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserMeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Daftar Pengguna Baru",
    dependencies=[Depends(rate_limit(lambda: settings.AUTH_REGISTER_RATE_LIMIT))],
)
def register(
    data: RegisterRequest,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
):
    """Mendaftarkan akun pengguna baru dengan validasi email dan password hash Argon2."""
    audit = AuditService(db)
    existing_user = db.query(User).filter(User.email == data.email).first()
    if existing_user:
        audit.log(
            action=AuditAction.AUTH_REGISTER,
            resource_type="auth",
            status=AuditStatus.FAILED,
            metadata={"email": data.email, "reason": "email_already_registered"},
            request=request,
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email sudah terdaftar.",
        )

    user = User(
        name=data.name,
        email=data.email,
        password_hash=hash_password(data.password),
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    audit.log(
        action=AuditAction.AUTH_REGISTER,
        resource_type="auth",
        status=AuditStatus.SUCCESS,
        user_id=user.id,
        resource_id=str(user.id),
        metadata={"email": user.email, "name": user.name},
        request=request,
    )

    return user


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Login Pengguna",
    dependencies=[Depends(rate_limit(lambda: settings.AUTH_LOGIN_RATE_LIMIT))],
)
def login(
    data: LoginRequest,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
):
    """Melakukan login dan menerbitkan JWT access token beserta opaque refresh token."""
    audit = AuditService(db)
    user = db.query(User).filter(User.email == data.email).first()
    if not user or not verify_password(data.password, user.password_hash):
        audit.log(
            action=AuditAction.AUTH_LOGIN,
            resource_type="auth",
            status=AuditStatus.FAILED,
            user_id=user.id if user else None,
            metadata={"email": data.email, "reason": "invalid_credentials"},
            request=request,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email atau password salah.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        audit.log(
            action=AuditAction.AUTH_LOGIN,
            resource_type="auth",
            status=AuditStatus.DENIED,
            user_id=user.id,
            metadata={"email": data.email, "reason": "inactive_user"},
            request=request,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Akun pengguna tidak aktif.",
        )

    # Buat access token & refresh token
    access_token = create_access_token(subject=str(user.id))
    raw_refresh_token = generate_refresh_token()
    token_hash = hash_refresh_token(raw_refresh_token)
    expires_at = datetime.now(timezone.utc) + timedelta(
        days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
    )

    db_refresh = RefreshToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=expires_at,
    )
    db.add(db_refresh)
    db.commit()

    audit.log(
        action=AuditAction.AUTH_LOGIN,
        resource_type="auth",
        status=AuditStatus.SUCCESS,
        user_id=user.id,
        resource_id=str(user.id),
        metadata={"email": user.email},
        request=request,
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=raw_refresh_token,
        token_type="bearer",
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Perbarui Access Token",
    dependencies=[Depends(rate_limit(lambda: settings.AUTH_REFRESH_RATE_LIMIT))],
)
def refresh_token(
    data: RefreshTokenRequest,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
):
    """Memperbarui access token dengan refresh token rotation & deteksi reuse."""
    audit = AuditService(db)
    token_hash = hash_refresh_token(data.refresh_token)
    db_refresh = (
        db.query(RefreshToken)
        .filter(RefreshToken.token_hash == token_hash)
        .first()
    )

    # Token reuse detection: Token exists in DB but is already revoked
    if db_refresh and db_refresh.is_revoked:
        # Revoke all active tokens for this user session family for security
        active_tokens = (
            db.query(RefreshToken)
            .filter(
                RefreshToken.user_id == db_refresh.user_id,
                RefreshToken.revoked_at.is_(None),
            )
            .all()
        )
        for t in active_tokens:
            t.revoke()
        db.commit()

        audit.log(
            action=AuditAction.AUTH_REFRESH,
            resource_type="auth",
            status=AuditStatus.DENIED,
            user_id=db_refresh.user_id,
            metadata={"reason": "revoked_token_reuse_detected"},
            request=request,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token tidak valid atau telah digunakan ulang. Silakan login kembali.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not db_refresh or not db_refresh.is_active:
        audit.log(
            action=AuditAction.AUTH_REFRESH,
            resource_type="auth",
            status=AuditStatus.FAILED,
            metadata={"reason": "invalid_or_expired_refresh_token"},
            request=request,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token tidak valid, sudah dicabut, atau kedaluwarsa.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.id == db_refresh.user_id).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Pengguna tidak aktif atau tidak ditemukan.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Token rotation: Cabut token lama
    db_refresh.revoke()
    db_refresh.mark_used()

    # Buat token baru
    new_access_token = create_access_token(subject=str(user.id))
    new_raw_refresh = generate_refresh_token()
    new_token_hash = hash_refresh_token(new_raw_refresh)
    new_expires_at = datetime.now(timezone.utc) + timedelta(
        days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
    )

    new_db_refresh = RefreshToken(
        user_id=user.id,
        token_hash=new_token_hash,
        expires_at=new_expires_at,
    )
    db.add(new_db_refresh)
    db.commit()

    audit.log(
        action=AuditAction.AUTH_REFRESH,
        resource_type="auth",
        status=AuditStatus.SUCCESS,
        user_id=user.id,
        resource_id=str(user.id),
        metadata={"user_id": str(user.id)},
        request=request,
    )

    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_raw_refresh,
        token_type="bearer",
    )


@router.post(
    "/logout",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Logout & Cabut Refresh Token",
)
def logout(
    data: LogoutRequest,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
):
    """Mencabut refresh token yang aktif."""
    token_hash = hash_refresh_token(data.refresh_token)
    db_refresh = (
        db.query(RefreshToken)
        .filter(RefreshToken.token_hash == token_hash)
        .first()
    )

    if db_refresh and db_refresh.revoked_at is None:
        db_refresh.revoke()
        db.commit()
        audit = AuditService(db)
        audit.log(
            action=AuditAction.AUTH_LOGOUT,
            resource_type="auth",
            status=AuditStatus.SUCCESS,
            user_id=db_refresh.user_id,
            resource_id=str(db_refresh.user_id),
            metadata={"user_id": str(db_refresh.user_id)},
            request=request,
        )

    return MessageResponse(message="Logout berhasil.")


@router.get(
    "/me",
    response_model=UserMeResponse,
    status_code=status.HTTP_200_OK,
    summary="Informasi Pengguna Saat Ini",
)
def get_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """Mengembalikan data profil pengguna yang sedang login tanpa membocorkan credential."""
    return current_user

