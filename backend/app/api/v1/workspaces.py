import uuid
from typing import List
from typing_extensions import Annotated
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.core.deps import get_current_active_user, RequireWorkspaceRole
from app.models.user import User
from app.models.workspace import Workspace
from app.models.workspace_member import WorkspaceMember, WorkspaceRole
from app.schemas.audit_log import AuditAction, AuditStatus
from app.schemas.workspace import (
    WorkspaceCreate,
    WorkspaceUpdate,
    WorkspaceListItem,
    WorkspaceDetailResponse,
)
from app.schemas.workspace_member import (
    WorkspaceMemberCreate,
    WorkspaceMemberRoleUpdate,
    WorkspaceMemberResponse,
)
from app.schemas.auth import MessageResponse
from app.services.audit_service import AuditService

router = APIRouter(prefix="/workspaces", tags=["Workspaces"])


# ==========================================
# 1. CREATE WORKSPACE
# ==========================================
@router.post(
    "",
    response_model=WorkspaceDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Buat Workspace Baru",
)
def create_workspace(
    data: WorkspaceCreate,
    request: Request,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Membuat workspace baru dan otomatis menjadikan current user sebagai OWNER."""
    workspace = Workspace(
        name=data.name,
        description=data.description,
        timezone=data.timezone,
    )
    db.add(workspace)
    db.flush()

    # Otomatis buat membership OWNER untuk pembuat workspace
    member = WorkspaceMember(
        workspace_id=workspace.id,
        user_id=current_user.id,
        role=WorkspaceRole.OWNER.value,
    )
    db.add(member)
    db.commit()
    db.refresh(workspace)

    audit = AuditService(db)
    audit.log(
        action=AuditAction.WORKSPACE_CREATED,
        resource_type="workspace",
        status=AuditStatus.SUCCESS,
        workspace_id=workspace.id,
        user_id=current_user.id,
        resource_id=str(workspace.id),
        metadata={"name": workspace.name},
        request=request,
    )

    return WorkspaceDetailResponse(
        id=workspace.id,
        name=workspace.name,
        description=workspace.description,
        timezone=workspace.timezone,
        role=WorkspaceRole.OWNER.value,
        created_at=workspace.created_at,
        updated_at=workspace.updated_at,
    )


# ==========================================
# 2. LIST WORKSPACES
# ==========================================
@router.get(
    "",
    response_model=List[WorkspaceListItem],
    status_code=status.HTTP_200_OK,
    summary="Daftar Workspace Pengguna",
)
def list_workspaces(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Mengembalikan semua workspace di mana current user terdaftar sebagai member."""
    memberships = (
        db.query(WorkspaceMember)
        .options(joinedload(WorkspaceMember.workspace))
        .filter(WorkspaceMember.user_id == current_user.id)
        .all()
    )

    items = []
    for m in memberships:
        ws = m.workspace
        items.append(
            WorkspaceListItem(
                id=ws.id,
                name=ws.name,
                description=ws.description,
                timezone=ws.timezone,
                role=m.role,
                created_at=ws.created_at,
                updated_at=ws.updated_at,
            )
        )
    return items


# ==========================================
# 3. GET WORKSPACE DETAIL
# ==========================================
@router.get(
    "/{workspace_id}",
    response_model=WorkspaceDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Detail Workspace",
)
def get_workspace_detail(
    workspace_id: uuid.UUID,
    membership: Annotated[
        WorkspaceMember,
        Depends(
            RequireWorkspaceRole(
                [
                    WorkspaceRole.OWNER,
                    WorkspaceRole.ADMIN,
                    WorkspaceRole.DEVELOPER,
                    WorkspaceRole.VIEWER,
                ]
            )
        ),
    ],
):
    """Mengambil detail workspace termasuk role pengguna saat ini."""
    ws = membership.workspace
    return WorkspaceDetailResponse(
        id=ws.id,
        name=ws.name,
        description=ws.description,
        timezone=ws.timezone,
        role=membership.role,
        created_at=ws.created_at,
        updated_at=ws.updated_at,
    )


# ==========================================
# 4. UPDATE WORKSPACE
# ==========================================
@router.patch(
    "/{workspace_id}",
    response_model=WorkspaceDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Perbarui Informasi Workspace",
)
def update_workspace(
    workspace_id: uuid.UUID,
    data: WorkspaceUpdate,
    request: Request,
    membership: Annotated[
        WorkspaceMember,
        Depends(
            RequireWorkspaceRole(
                [WorkspaceRole.OWNER, WorkspaceRole.ADMIN]
            )
        ),
    ],
    db: Annotated[Session, Depends(get_db)],
):
    """Memperbarui informasi workspace (hanya untuk OWNER dan ADMIN)."""
    ws = membership.workspace

    if data.name is not None:
        ws.name = data.name
    if data.description is not None:
        ws.description = data.description
    if data.timezone is not None:
        ws.timezone = data.timezone

    db.commit()
    db.refresh(ws)

    audit = AuditService(db)
    audit.log(
        action=AuditAction.WORKSPACE_UPDATED,
        resource_type="workspace",
        status=AuditStatus.SUCCESS,
        workspace_id=ws.id,
        user_id=membership.user_id,
        resource_id=str(ws.id),
        metadata={"name": ws.name},
        request=request,
    )

    return WorkspaceDetailResponse(
        id=ws.id,
        name=ws.name,
        description=ws.description,
        timezone=ws.timezone,
        role=membership.role,
        created_at=ws.created_at,
        updated_at=ws.updated_at,
    )


# ==========================================
# 5. LIST MEMBERS
# ==========================================
@router.get(
    "/{workspace_id}/members",
    response_model=List[WorkspaceMemberResponse],
    status_code=status.HTTP_200_OK,
    summary="Daftar Member Workspace",
)
def list_workspace_members(
    workspace_id: uuid.UUID,
    membership: Annotated[
        WorkspaceMember,
        Depends(
            RequireWorkspaceRole(
                [
                    WorkspaceRole.OWNER,
                    WorkspaceRole.ADMIN,
                    WorkspaceRole.DEVELOPER,
                    WorkspaceRole.VIEWER,
                ]
            )
        ),
    ],
    db: Annotated[Session, Depends(get_db)],
):
    """Mengambil seluruh daftar anggota workspace."""
    members = (
        db.query(WorkspaceMember)
        .options(joinedload(WorkspaceMember.user))
        .filter(WorkspaceMember.workspace_id == workspace_id)
        .order_by(WorkspaceMember.created_at.asc())
        .all()
    )

    return [
        WorkspaceMemberResponse(
            id=m.id,
            user_id=m.user.id,
            name=m.user.name,
            email=m.user.email,
            role=m.role,
            created_at=m.created_at,
        )
        for m in members
    ]


# ==========================================
# 6. ADD MEMBER
# ==========================================
@router.post(
    "/{workspace_id}/members",
    response_model=WorkspaceMemberResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Tambah Member ke Workspace",
)
def add_workspace_member(
    workspace_id: uuid.UUID,
    data: WorkspaceMemberCreate,
    request: Request,
    membership: Annotated[
        WorkspaceMember,
        Depends(
            RequireWorkspaceRole(
                [WorkspaceRole.OWNER, WorkspaceRole.ADMIN]
            )
        ),
    ],
    db: Annotated[Session, Depends(get_db)],
):
    """Menambahkan user yang sudah terdaftar sebagai member workspace."""
    # Aturan: Tidak boleh menambahkan OWNER langsung
    if data.role == WorkspaceRole.OWNER:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role OWNER tidak dapat ditambahkan langsung. Fitur transfer kepemilikan belum didukung.",
        )

    # Aturan: ADMIN hanya boleh menambahkan DEVELOPER atau VIEWER
    if membership.role == WorkspaceRole.ADMIN.value:
        if data.role not in [WorkspaceRole.DEVELOPER, WorkspaceRole.VIEWER]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin hanya dapat menambahkan member dengan role DEVELOPER atau VIEWER.",
            )

    # Cari target user berdasarkan email
    target_user = (
        db.query(User).filter(User.email == data.email).first()
    )
    if not target_user or not target_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pengguna dengan email tersebut tidak ditemukan atau tidak aktif.",
        )

    # Cek apakah sudah menjadi member
    existing = (
        db.query(WorkspaceMember)
        .filter(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == target_user.id,
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Pengguna sudah menjadi member di workspace ini.",
        )

    new_member = WorkspaceMember(
        workspace_id=workspace_id,
        user_id=target_user.id,
        role=data.role.value,
    )
    db.add(new_member)
    db.commit()
    db.refresh(new_member)

    audit = AuditService(db)
    audit.log(
        action=AuditAction.WORKSPACE_MEMBER_ADDED,
        resource_type="workspace_member",
        status=AuditStatus.SUCCESS,
        workspace_id=workspace_id,
        user_id=membership.user_id,
        resource_id=str(new_member.id),
        metadata={"target_email": target_user.email, "role": new_member.role},
        request=request,
    )

    return WorkspaceMemberResponse(
        id=new_member.id,
        user_id=target_user.id,
        name=target_user.name,
        email=target_user.email,
        role=new_member.role,
        created_at=new_member.created_at,
    )


# ==========================================
# 7. SELF LEAVE WORKSPACE (DELETE /members/me)
# ==========================================
@router.delete(
    "/{workspace_id}/members/me",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Keluar dari Workspace",
)
def leave_workspace(
    workspace_id: uuid.UUID,
    request: Request,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """User keluar dari keanggotaan workspace miliknya."""
    membership = (
        db.query(WorkspaceMember)
        .filter(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == current_user.id,
        )
        .first()
    )
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace tidak ditemukan.",
        )

    # Aturan: Jika user adalah OWNER tunggal, tidak boleh keluar
    if membership.role == WorkspaceRole.OWNER.value:
        owner_count = (
            db.query(WorkspaceMember)
            .filter(
                WorkspaceMember.workspace_id == workspace_id,
                WorkspaceMember.role == WorkspaceRole.OWNER.value,
            )
            .count()
        )
        if owner_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Owner tunggal tidak dapat meninggalkan workspace. Silakan jadikan member lain sebagai Owner terlebih dahulu.",
            )

    db.delete(membership)
    db.commit()

    audit = AuditService(db)
    audit.log(
        action=AuditAction.WORKSPACE_MEMBER_REMOVED,
        resource_type="workspace_member",
        status=AuditStatus.SUCCESS,
        workspace_id=workspace_id,
        user_id=current_user.id,
        resource_id=str(current_user.id),
        metadata={"action": "self_leave"},
        request=request,
    )

    return MessageResponse(message="Berhasil keluar dari workspace.")


# ==========================================
# 8. UPDATE MEMBER ROLE
# ==========================================
@router.patch(
    "/{workspace_id}/members/{user_id}",
    response_model=WorkspaceMemberResponse,
    status_code=status.HTTP_200_OK,
    summary="Ubah Role Member",
)
def update_member_role(
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
    data: WorkspaceMemberRoleUpdate,
    request: Request,
    membership: Annotated[
        WorkspaceMember,
        Depends(
            RequireWorkspaceRole(
                [WorkspaceRole.OWNER, WorkspaceRole.ADMIN]
            )
        ),
    ],
    db: Annotated[Session, Depends(get_db)],
):
    """Mengubah role member workspace."""
    # Cari target member
    target_member = (
        db.query(WorkspaceMember)
        .options(joinedload(WorkspaceMember.user))
        .filter(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user_id,
        )
        .first()
    )
    if not target_member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member tidak ditemukan di workspace ini.",
        )

    # Aturan: Tidak boleh mempromosikan menjadi OWNER
    if data.role == WorkspaceRole.OWNER:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tidak dapat mengubah member menjadi role OWNER.",
        )

    # Aturan: Role OWNER target tidak boleh diubah
    if target_member.role == WorkspaceRole.OWNER.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role OWNER tidak dapat diubah.",
        )

    # Aturan khusus ADMIN
    if membership.role == WorkspaceRole.ADMIN.value:
        if target_member.role == WorkspaceRole.ADMIN.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin tidak memiliki izin untuk mengubah role sesama Admin.",
            )
        if data.role not in [WorkspaceRole.DEVELOPER, WorkspaceRole.VIEWER]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin hanya dapat mengubah role menjadi DEVELOPER atau VIEWER.",
            )

    old_role = target_member.role
    target_member.role = data.role.value
    db.commit()
    db.refresh(target_member)

    audit = AuditService(db)
    audit.log(
        action=AuditAction.WORKSPACE_ROLE_CHANGED,
        resource_type="workspace_member",
        status=AuditStatus.SUCCESS,
        workspace_id=workspace_id,
        user_id=membership.user_id,
        resource_id=str(target_member.id),
        metadata={"target_user_id": str(target_member.user_id), "old_role": old_role, "new_role": target_member.role},
        request=request,
    )

    return WorkspaceMemberResponse(
        id=target_member.id,
        user_id=target_member.user.id,
        name=target_member.user.name,
        email=target_member.user.email,
        role=target_member.role,
        created_at=target_member.created_at,
    )


# ==========================================
# 9. REMOVE MEMBER
# ==========================================
@router.delete(
    "/{workspace_id}/members/{user_id}",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Hapus Member dari Workspace",
)
def remove_workspace_member(
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
    request: Request,
    membership: Annotated[
        WorkspaceMember,
        Depends(
            RequireWorkspaceRole(
                [WorkspaceRole.OWNER, WorkspaceRole.ADMIN]
            )
        ),
    ],
    db: Annotated[Session, Depends(get_db)],
):
    """Menghapus member dari workspace."""
    target_member = (
        db.query(WorkspaceMember)
        .filter(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user_id,
        )
        .first()
    )
    if not target_member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member tidak ditemukan di workspace ini.",
        )

    # Aturan: Target OWNER tidak boleh dihapus
    if target_member.role == WorkspaceRole.OWNER.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Owner tidak dapat dihapus dari workspace.",
        )

    # Aturan khusus ADMIN: Hanya boleh hapus DEVELOPER dan VIEWER
    if membership.role == WorkspaceRole.ADMIN.value:
        if target_member.role not in [
            WorkspaceRole.DEVELOPER.value,
            WorkspaceRole.VIEWER.value,
        ]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin hanya dapat menghapus member dengan role DEVELOPER atau VIEWER.",
            )

    db.delete(target_member)
    db.commit()

    audit = AuditService(db)
    audit.log(
        action=AuditAction.WORKSPACE_MEMBER_REMOVED,
        resource_type="workspace_member",
        status=AuditStatus.SUCCESS,
        workspace_id=workspace_id,
        user_id=membership.user_id,
        resource_id=str(user_id),
        metadata={"target_user_id": str(user_id)},
        request=request,
    )

    return MessageResponse(message="Member berhasil dihapus dari workspace.")
