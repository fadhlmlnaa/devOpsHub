import uuid
from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import RequireWorkspaceRole
from app.models.server import Server
from app.models.user import User
from app.models.workspace_member import WorkspaceRole
from app.schemas.service import (
    ServiceActionRequest,
    ServiceActionResponse,
    ServiceDetailResponse,
    ServiceListResponse,
)
from app.services.service_management import (
    ServiceManagementService,
    get_service_management_service,
)

router = APIRouter(
    prefix="/workspaces/{workspace_id}/servers/{server_id}/services",
    tags=["Services"],
)


def _get_server_or_404(db: Session, workspace_id: uuid.UUID, server_id: uuid.UUID) -> Server:
    server = (
        db.query(Server)
        .filter(Server.id == server_id, Server.workspace_id == workspace_id)
        .first()
    )
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server tidak ditemukan dalam workspace ini.",
        )
    return server


@router.get(
    "",
    response_model=ServiceListResponse,
    summary="Daftar Systemd Services pada Server",
)
async def list_services(
    workspace_id: uuid.UUID,
    server_id: uuid.UUID,
    current_user_and_role: Annotated[
        tuple[User, WorkspaceRole],
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
    state: Optional[str] = Query(None, description="Filter status: active, inactive, failed, all"),
    limit: int = Query(100, ge=1, le=200, description="Batas jumlah service (maks 200)"),
    db: Session = Depends(get_db),
    service_svc: ServiceManagementService = Depends(get_service_management_service),
):
    server = _get_server_or_404(db, workspace_id, server_id)
    filter_state = None if state == "all" else state
    return await service_svc.list_services(server=server, state=filter_state, limit=limit)


@router.get(
    "/{service_name}",
    response_model=ServiceDetailResponse,
    summary="Detail Status Systemd Service",
)
async def get_service(
    workspace_id: uuid.UUID,
    server_id: uuid.UUID,
    service_name: str,
    current_user_and_role: Annotated[
        tuple[User, WorkspaceRole],
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
    db: Session = Depends(get_db),
    service_svc: ServiceManagementService = Depends(get_service_management_service),
):
    server = _get_server_or_404(db, workspace_id, server_id)
    return await service_svc.get_service(server=server, service_name=service_name)


@router.post(
    "/{service_name}/start",
    response_model=ServiceActionResponse,
    summary="Start Systemd Service",
)
async def start_service(
    workspace_id: uuid.UUID,
    server_id: uuid.UUID,
    service_name: str,
    payload: ServiceActionRequest,
    current_user_and_role: Annotated[
        tuple[User, WorkspaceRole],
        Depends(RequireWorkspaceRole([WorkspaceRole.OWNER, WorkspaceRole.ADMIN])),
    ],
    db: Session = Depends(get_db),
    service_svc: ServiceManagementService = Depends(get_service_management_service),
):
    server = _get_server_or_404(db, workspace_id, server_id)
    return await service_svc.execute_action(
        server=server,
        service_name=service_name,
        action="start",
        confirm=payload.confirm,
    )


@router.post(
    "/{service_name}/stop",
    response_model=ServiceActionResponse,
    summary="Stop Systemd Service",
)
async def stop_service(
    workspace_id: uuid.UUID,
    server_id: uuid.UUID,
    service_name: str,
    payload: ServiceActionRequest,
    current_user_and_role: Annotated[
        tuple[User, WorkspaceRole],
        Depends(RequireWorkspaceRole([WorkspaceRole.OWNER, WorkspaceRole.ADMIN])),
    ],
    db: Session = Depends(get_db),
    service_svc: ServiceManagementService = Depends(get_service_management_service),
):
    server = _get_server_or_404(db, workspace_id, server_id)
    return await service_svc.execute_action(
        server=server,
        service_name=service_name,
        action="stop",
        confirm=payload.confirm,
    )


@router.post(
    "/{service_name}/restart",
    response_model=ServiceActionResponse,
    summary="Restart Systemd Service",
)
async def restart_service(
    workspace_id: uuid.UUID,
    server_id: uuid.UUID,
    service_name: str,
    payload: ServiceActionRequest,
    current_user_and_role: Annotated[
        tuple[User, WorkspaceRole],
        Depends(RequireWorkspaceRole([WorkspaceRole.OWNER, WorkspaceRole.ADMIN])),
    ],
    db: Session = Depends(get_db),
    service_svc: ServiceManagementService = Depends(get_service_management_service),
):
    server = _get_server_or_404(db, workspace_id, server_id)
    return await service_svc.execute_action(
        server=server,
        service_name=service_name,
        action="restart",
        confirm=payload.confirm,
    )


@router.post(
    "/{service_name}/reload",
    response_model=ServiceActionResponse,
    summary="Reload Systemd Service",
)
async def reload_service(
    workspace_id: uuid.UUID,
    server_id: uuid.UUID,
    service_name: str,
    payload: ServiceActionRequest,
    current_user_and_role: Annotated[
        tuple[User, WorkspaceRole],
        Depends(RequireWorkspaceRole([WorkspaceRole.OWNER, WorkspaceRole.ADMIN])),
    ],
    db: Session = Depends(get_db),
    service_svc: ServiceManagementService = Depends(get_service_management_service),
):
    server = _get_server_or_404(db, workspace_id, server_id)
    return await service_svc.execute_action(
        server=server,
        service_name=service_name,
        action="reload",
        confirm=payload.confirm,
    )
