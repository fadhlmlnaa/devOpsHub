from typing import List, Optional
import uuid
from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import get_current_user, RequireWorkspaceRole
from app.core.rate_limit import rate_limit
from app.models.user import User
from app.models.workspace_member import WorkspaceMember, WorkspaceRole
from app.schemas.audit_log import AuditAction, AuditStatus
from app.schemas.backup import (
    BackupConfigCreate,
    BackupConfigUpdate,
    BackupConfigResponse,
    BackupTriggerRequest,
    BackupVerifyRequest,
    BackupVerifyResponse,
    BackupResponse,
    BackupListResponse,
    BackupLogsResponse,
)
from app.services.audit_service import AuditService
from app.services.backup_management import BackupManagementService

router = APIRouter(tags=["Backup Management"])

ALL_ROLES = [
    WorkspaceRole.OWNER,
    WorkspaceRole.ADMIN,
    WorkspaceRole.DEVELOPER,
    WorkspaceRole.VIEWER,
]

MUTATION_ROLES = [
    WorkspaceRole.OWNER,
    WorkspaceRole.ADMIN,
]


# --- Backup Configuration APIs ---

@router.get(
    "/workspaces/{workspace_id}/backup-configs",
    response_model=List[BackupConfigResponse],
    summary="List backup configurations",
)
def list_backup_configs(
    workspace_id: uuid.UUID,
    environment_id: Optional[uuid.UUID] = Query(None, description="Filter by environment ID"),
    server_id: Optional[uuid.UUID] = Query(None, description="Filter by server ID"),
    db: Session = Depends(get_db),
    member: WorkspaceMember = Depends(RequireWorkspaceRole(ALL_ROLES)),
):
    """Retrieves all registered backup configurations in the workspace."""
    service = BackupManagementService(db)
    return service.list_backup_configs(
        workspace_id=workspace_id,
        member=member,
        environment_id=environment_id,
        server_id=server_id,
    )


@router.post(
    "/workspaces/{workspace_id}/backup-configs",
    response_model=BackupConfigResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create backup configuration",
)
def create_backup_config(
    workspace_id: uuid.UUID,
    payload: BackupConfigCreate,
    db: Session = Depends(get_db),
    member: WorkspaceMember = Depends(RequireWorkspaceRole(MUTATION_ROLES)),
):
    """Creates a new backup configuration (ADMIN/OWNER only)."""
    service = BackupManagementService(db)
    return service.create_backup_config(
        workspace_id=workspace_id,
        data=payload,
        member=member,
    )


@router.get(
    "/workspaces/{workspace_id}/backup-configs/{config_id}",
    response_model=BackupConfigResponse,
    summary="Get backup configuration detail",
)
def get_backup_config(
    workspace_id: uuid.UUID,
    config_id: uuid.UUID,
    db: Session = Depends(get_db),
    member: WorkspaceMember = Depends(RequireWorkspaceRole(ALL_ROLES)),
):
    """Retrieves detailed backup configuration."""
    service = BackupManagementService(db)
    return service.get_backup_config(
        workspace_id=workspace_id,
        config_id=config_id,
        member=member,
    )


@router.patch(
    "/workspaces/{workspace_id}/backup-configs/{config_id}",
    response_model=BackupConfigResponse,
    summary="Update backup configuration",
)
def update_backup_config(
    workspace_id: uuid.UUID,
    config_id: uuid.UUID,
    payload: BackupConfigUpdate,
    db: Session = Depends(get_db),
    member: WorkspaceMember = Depends(RequireWorkspaceRole(MUTATION_ROLES)),
):
    """Updates an existing backup configuration (ADMIN/OWNER only)."""
    service = BackupManagementService(db)
    return service.update_backup_config(
        workspace_id=workspace_id,
        config_id=config_id,
        data=payload,
        member=member,
    )


@router.delete(
    "/workspaces/{workspace_id}/backup-configs/{config_id}",
    summary="Delete backup configuration",
)
def delete_backup_config(
    workspace_id: uuid.UUID,
    config_id: uuid.UUID,
    db: Session = Depends(get_db),
    member: WorkspaceMember = Depends(RequireWorkspaceRole(MUTATION_ROLES)),
):
    """Deletes a backup configuration (ADMIN/OWNER only)."""
    service = BackupManagementService(db)
    return service.delete_backup_config(
        workspace_id=workspace_id,
        config_id=config_id,
        member=member,
    )


# --- Backup Execution & Verification APIs ---

@router.post(
    "/workspaces/{workspace_id}/backup-configs/{config_id}/run",
    response_model=BackupResponse,
    summary="Trigger a controlled backup execution",
    dependencies=[Depends(rate_limit(lambda: settings.OPERATION_RATE_LIMIT))],
)
async def trigger_backup(
    workspace_id: uuid.UUID,
    config_id: uuid.UUID,
    payload: BackupTriggerRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    member: WorkspaceMember = Depends(RequireWorkspaceRole(MUTATION_ROLES)),
):
    """Triggers a controlled backup execution on the target server (ADMIN/OWNER only)."""
    service = BackupManagementService(db)
    res = await service.trigger_backup(
        workspace_id=workspace_id,
        config_id=config_id,
        member=member,
        user_id=current_user.id,
        confirm=payload.confirm,
    )
    audit = AuditService(db)
    action_type = AuditAction.BACKUP_SUCCEEDED if res.status == "SUCCESS" else (
        AuditAction.BACKUP_FAILED if res.status == "FAILED" else AuditAction.BACKUP_STARTED
    )
    audit.log(
        action=action_type,
        resource_type="backup",
        status=AuditStatus.SUCCESS if res.status == "SUCCESS" else (
            AuditStatus.FAILED if res.status == "FAILED" else AuditStatus.SUCCESS
        ),
        workspace_id=workspace_id,
        user_id=current_user.id,
        resource_id=str(res.id),
        environment_id=res.environment_id,
        server_id=res.server_id,
        metadata={"backup_id": str(res.id), "status": res.status, "backup_type": res.backup_type},
        request=request,
    )
    return res


@router.post(
    "/workspaces/{workspace_id}/backups/{backup_id}/verify",
    response_model=BackupVerifyResponse,
    summary="Verify backup integrity via SHA-256 checksum",
    dependencies=[Depends(rate_limit(lambda: settings.OPERATION_RATE_LIMIT))],
)
async def verify_backup(
    workspace_id: uuid.UUID,
    backup_id: uuid.UUID,
    request: Request,
    payload: BackupVerifyRequest = BackupVerifyRequest(confirm=True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    member: WorkspaceMember = Depends(RequireWorkspaceRole(MUTATION_ROLES)),
):
    """Verifies that the backup file exists on the server and matches stored SHA-256 (ADMIN/OWNER only)."""
    service = BackupManagementService(db)
    res = await service.verify_backup(
        workspace_id=workspace_id,
        backup_id=backup_id,
        member=member,
        confirm=payload.confirm,
    )
    audit = AuditService(db)
    audit.log(
        action=AuditAction.BACKUP_VERIFIED,
        resource_type="backup",
        status=AuditStatus.SUCCESS if res.verified else AuditStatus.FAILED,
        workspace_id=workspace_id,
        user_id=current_user.id,
        resource_id=str(backup_id),
        metadata={"backup_id": str(backup_id), "verified": res.verified, "message": res.message},
        request=request,
    )
    return res


# --- Backup History & Logs APIs ---

@router.get(
    "/workspaces/{workspace_id}/backups",
    response_model=BackupListResponse,
    summary="List backup history",
)
def list_backups(
    workspace_id: uuid.UUID,
    environment_id: Optional[uuid.UUID] = Query(None, description="Filter by environment ID"),
    server_id: Optional[uuid.UUID] = Query(None, description="Filter by server ID"),
    backup_config_id: Optional[uuid.UUID] = Query(None, description="Filter by backup config ID"),
    backup_type: Optional[str] = Query(None, description="Filter by backup type (POSTGRESQL, FILESYSTEM, DOCKER_VOLUME)"),
    status: Optional[str] = Query(None, description="Filter by status (PENDING, RUNNING, SUCCESS, FAILED, CANCELLED)"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    member: WorkspaceMember = Depends(RequireWorkspaceRole(ALL_ROLES)),
):
    """Retrieves paginated backup history for the workspace."""
    service = BackupManagementService(db)
    return service.list_backups(
        workspace_id=workspace_id,
        member=member,
        environment_id=environment_id,
        server_id=server_id,
        backup_config_id=backup_config_id,
        backup_type=backup_type,
        status_filter=status,
        page=page,
        limit=limit,
    )


@router.get(
    "/workspaces/{workspace_id}/backups/{backup_id}",
    response_model=BackupResponse,
    summary="Get backup execution detail",
)
def get_backup(
    workspace_id: uuid.UUID,
    backup_id: uuid.UUID,
    db: Session = Depends(get_db),
    member: WorkspaceMember = Depends(RequireWorkspaceRole(ALL_ROLES)),
):
    """Retrieves details of a specific backup execution."""
    service = BackupManagementService(db)
    return service.get_backup(
        workspace_id=workspace_id,
        backup_id=backup_id,
        member=member,
    )


@router.get(
    "/workspaces/{workspace_id}/backups/{backup_id}/logs",
    response_model=BackupLogsResponse,
    summary="Get backup logs",
)
def get_backup_logs(
    workspace_id: uuid.UUID,
    backup_id: uuid.UUID,
    lines: int = Query(100, ge=10, le=1000, description="Number of log lines to retrieve"),
    db: Session = Depends(get_db),
    member: WorkspaceMember = Depends(RequireWorkspaceRole(ALL_ROLES)),
):
    """Retrieves logs of a specific backup execution."""
    service = BackupManagementService(db)
    return service.get_backup_logs(
        workspace_id=workspace_id,
        backup_id=backup_id,
        member=member,
        lines=lines,
    )
