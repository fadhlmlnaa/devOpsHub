import uuid
from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import RequireWorkspaceRole
from app.models.server import Server
from app.models.user import User
from app.models.workspace_member import WorkspaceRole
from app.schemas.log import LogResponse
from app.services.log_management import (
    LogManagementService,
    get_log_management_service,
)

router = APIRouter(
    prefix="/workspaces/{workspace_id}/servers/{server_id}/services/{service_name}/logs",
    tags=["Logs"],
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
    response_model=LogResponse,
    summary="Ambil Log Service (Systemd Journal)",
)
async def get_service_logs(
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
    lines: int = Query(100, ge=10, le=1000, description="Jumlah baris log (10 - 1000)"),
    since: Optional[str] = Query(
        None,
        pattern="^(5m|10m|30m|1h|6h|12h|24h)$",
        description="Filter rentang waktu: 5m, 10m, 30m, 1h, 6h, 12h, 24h",
    ),
    db: Session = Depends(get_db),
    log_svc: LogManagementService = Depends(get_log_management_service),
):
    server = _get_server_or_404(db, workspace_id, server_id)
    return await log_svc.get_service_logs(
        server=server,
        service_name=service_name,
        lines=lines,
        since=since,
    )
