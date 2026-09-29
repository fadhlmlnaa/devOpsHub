import uuid
from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import RequireWorkspaceRole
from app.models.user import User
from app.models.workspace_member import WorkspaceRole
from app.models.environment import Environment
from app.models.server import Server
from app.schemas.environment import (
    EnvironmentCreate,
    EnvironmentUpdate,
    EnvironmentResponse,
)

router = APIRouter(
    prefix="/workspaces/{workspace_id}/environments",
    tags=["Environments"],
)


@router.get(
    "",
    response_model=List[EnvironmentResponse],
    summary="Daftar Environment dalam Workspace",
)
def list_environments(
    workspace_id: uuid.UUID,
    auth: Annotated[
        tuple[User, WorkspaceRole],
        Depends(
            RequireWorkspaceRole([
                WorkspaceRole.OWNER,
                WorkspaceRole.ADMIN,
                WorkspaceRole.DEVELOPER,
                WorkspaceRole.VIEWER,
            ])
        ),
    ],
    db: Annotated[Session, Depends(get_db)],
):
    """Mengambil daftar seluruh environment yang berada di dalam workspace."""
    environments = (
        db.query(Environment)
        .filter(Environment.workspace_id == workspace_id)
        .order_by(Environment.created_at.asc())
        .all()
    )

    results = []
    for env in environments:
        server_count = db.query(Server).filter(Server.environment_id == env.id).count()
        results.append(
            EnvironmentResponse(
                id=env.id,
                workspace_id=env.workspace_id,
                name=env.name,
                key=env.key,
                description=env.description,
                server_count=server_count,
                created_at=env.created_at,
                updated_at=env.updated_at,
            )
        )
    return results


@router.post(
    "",
    response_model=EnvironmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Buat Environment Baru (OWNER, ADMIN)",
)
def create_environment(
    workspace_id: uuid.UUID,
    data: EnvironmentCreate,
    auth: Annotated[
        tuple[User, WorkspaceRole],
        Depends(
            RequireWorkspaceRole([
                WorkspaceRole.OWNER,
                WorkspaceRole.ADMIN,
            ])
        ),
    ],
    db: Annotated[Session, Depends(get_db)],
):
    """Membuat environment baru dalam workspace. Key harus unik per workspace."""
    existing_key = (
        db.query(Environment)
        .filter(
            Environment.workspace_id == workspace_id,
            Environment.key == data.key,
        )
        .first()
    )
    if existing_key:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Environment dengan key '{data.key}' sudah ada di workspace ini.",
        )

    environment = Environment(
        workspace_id=workspace_id,
        name=data.name,
        key=data.key,
        description=data.description,
    )
    db.add(environment)
    db.commit()
    db.refresh(environment)

    return EnvironmentResponse(
        id=environment.id,
        workspace_id=environment.workspace_id,
        name=environment.name,
        key=environment.key,
        description=environment.description,
        server_count=0,
        created_at=environment.created_at,
        updated_at=environment.updated_at,
    )


@router.get(
    "/{environment_id}",
    response_model=EnvironmentResponse,
    summary="Detail Environment",
)
def get_environment(
    workspace_id: uuid.UUID,
    environment_id: uuid.UUID,
    auth: Annotated[
        tuple[User, WorkspaceRole],
        Depends(
            RequireWorkspaceRole([
                WorkspaceRole.OWNER,
                WorkspaceRole.ADMIN,
                WorkspaceRole.DEVELOPER,
                WorkspaceRole.VIEWER,
            ])
        ),
    ],
    db: Annotated[Session, Depends(get_db)],
):
    """Mengambil detail satu environment dalam workspace."""
    environment = (
        db.query(Environment)
        .filter(
            Environment.id == environment_id,
            Environment.workspace_id == workspace_id,
        )
        .first()
    )
    if not environment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Environment tidak ditemukan dalam workspace ini.",
        )

    server_count = db.query(Server).filter(Server.environment_id == environment.id).count()
    return EnvironmentResponse(
        id=environment.id,
        workspace_id=environment.workspace_id,
        name=environment.name,
        key=environment.key,
        description=environment.description,
        server_count=server_count,
        created_at=environment.created_at,
        updated_at=environment.updated_at,
    )


@router.patch(
    "/{environment_id}",
    response_model=EnvironmentResponse,
    summary="Update Environment (OWNER, ADMIN)",
)
def update_environment(
    workspace_id: uuid.UUID,
    environment_id: uuid.UUID,
    data: EnvironmentUpdate,
    auth: Annotated[
        tuple[User, WorkspaceRole],
        Depends(
            RequireWorkspaceRole([
                WorkspaceRole.OWNER,
                WorkspaceRole.ADMIN,
            ])
        ),
    ],
    db: Annotated[Session, Depends(get_db)],
):
    """Mengubah nama atau deskripsi environment."""
    environment = (
        db.query(Environment)
        .filter(
            Environment.id == environment_id,
            Environment.workspace_id == workspace_id,
        )
        .first()
    )
    if not environment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Environment tidak ditemukan dalam workspace ini.",
        )

    if data.name is not None:
        environment.name = data.name
    if data.description is not None:
        environment.description = data.description

    db.commit()
    db.refresh(environment)

    server_count = db.query(Server).filter(Server.environment_id == environment.id).count()
    return EnvironmentResponse(
        id=environment.id,
        workspace_id=environment.workspace_id,
        name=environment.name,
        key=environment.key,
        description=environment.description,
        server_count=server_count,
        created_at=environment.created_at,
        updated_at=environment.updated_at,
    )


@router.delete(
    "/{environment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Hapus Environment (OWNER, ADMIN)",
)
def delete_environment(
    workspace_id: uuid.UUID,
    environment_id: uuid.UUID,
    auth: Annotated[
        tuple[User, WorkspaceRole],
        Depends(
            RequireWorkspaceRole([
                WorkspaceRole.OWNER,
                WorkspaceRole.ADMIN,
            ])
        ),
    ],
    db: Annotated[Session, Depends(get_db)],
):
    """Menghapus environment. Ditolak jika masih terdapat server di dalamnya."""
    environment = (
        db.query(Environment)
        .filter(
            Environment.id == environment_id,
            Environment.workspace_id == workspace_id,
        )
        .first()
    )
    if not environment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Environment tidak ditemukan dalam workspace ini.",
        )

    server_count = db.query(Server).filter(Server.environment_id == environment.id).count()
    if server_count > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Tidak dapat menghapus environment yang masih memiliki server. Hapus atau pindahkan server terlebih dahulu.",
        )

    db.delete(environment)
    db.commit()
    return None
