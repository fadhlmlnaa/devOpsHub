import uuid
from datetime import datetime
from typing import Annotated, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import RequireWorkspaceRole
from app.models.workspace_member import WorkspaceMember, WorkspaceRole
from app.schemas.audit_log import AuditLogListResponse
from app.services.audit_service import AuditService

router = APIRouter(prefix="/workspaces", tags=["Audit Logs"])


@router.get(
    "/{workspace_id}/audit-logs",
    response_model=AuditLogListResponse,
    status_code=status.HTTP_200_OK,
    summary="Daftar Audit Logs Workspace",
)
def list_workspace_audit_logs(
    workspace_id: uuid.UUID,
    membership: Annotated[
        WorkspaceMember,
        Depends(RequireWorkspaceRole([WorkspaceRole.OWNER, WorkspaceRole.ADMIN])),
    ],
    db: Annotated[Session, Depends(get_db)],
    action: Optional[str] = Query(None, description="Filter by action name"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status (SUCCESS, FAILED, DENIED)"),
    user_id: Optional[uuid.UUID] = Query(None, description="Filter by user ID"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    server_id: Optional[uuid.UUID] = Query(None, description="Filter by server ID"),
    environment_id: Optional[uuid.UUID] = Query(None, description="Filter by environment ID"),
    start_date: Optional[datetime] = Query(None, description="Filter logs starting from datetime"),
    end_date: Optional[datetime] = Query(None, description="Filter logs up to datetime"),
    limit: int = Query(50, ge=1, le=100, description="Pagination limit (max 100)"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
):
    """Mengambil daftar audit log untuk workspace tertentu. Hanya dapat diakses oleh OWNER dan ADMIN."""
    audit_service = AuditService(db)
    items, total = audit_service.get_logs(
        workspace_id=workspace_id,
        action=action,
        status=status_filter,
        user_id=user_id,
        resource_type=resource_type,
        server_id=server_id,
        environment_id=environment_id,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset,
    )

    return AuditLogListResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )
