import logging
from typing import List, Optional
import uuid
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, RequireWorkspaceRole
from app.models.user import User
from app.models.workspace_member import WorkspaceMember, WorkspaceRole
from app.schemas.deployment import (
    DeploymentConfigCreate,
    DeploymentConfigUpdate,
    DeploymentConfigResponse,
    DeploymentTriggerRequest,
    DeploymentResponse,
    DeploymentListResponse,
    DeploymentLogsResponse,
)
from app.services.deployment_management import DeploymentManagementService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Deployment Management"])

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


# --- Deployment Configs API ---

@router.get(
    "/workspaces/{workspace_id}/deployment-configs",
    response_model=List[DeploymentConfigResponse],
    summary="List deployment configurations",
)
def list_deployment_configs(
    workspace_id: uuid.UUID,
    environment_id: Optional[uuid.UUID] = Query(None, description="Filter by environment ID"),
    server_id: Optional[uuid.UUID] = Query(None, description="Filter by server ID"),
    db: Session = Depends(get_db),
    member: WorkspaceMember = Depends(RequireWorkspaceRole(ALL_ROLES)),
):
    """Lists all deployment configurations registered in the workspace."""
    service = DeploymentManagementService(db)
    return service.list_deployment_configs(
        workspace_id=workspace_id,
        member=member,
        environment_id=environment_id,
        server_id=server_id,
    )


@router.post(
    "/workspaces/{workspace_id}/deployment-configs",
    response_model=DeploymentConfigResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a deployment configuration",
)
def create_deployment_config(
    workspace_id: uuid.UUID,
    payload: DeploymentConfigCreate,
    db: Session = Depends(get_db),
    member: WorkspaceMember = Depends(RequireWorkspaceRole(MUTATION_ROLES)),
):
    """Registers a new deployment configuration in the workspace (ADMIN/OWNER only)."""
    service = DeploymentManagementService(db)
    return service.create_deployment_config(
        workspace_id=workspace_id,
        data=payload,
        member=member,
    )


@router.get(
    "/workspaces/{workspace_id}/deployment-configs/{config_id}",
    response_model=DeploymentConfigResponse,
    summary="Get deployment configuration details",
)
def get_deployment_config(
    workspace_id: uuid.UUID,
    config_id: uuid.UUID,
    db: Session = Depends(get_db),
    member: WorkspaceMember = Depends(RequireWorkspaceRole(ALL_ROLES)),
):
    """Retrieves detailed deployment configuration."""
    service = DeploymentManagementService(db)
    return service.get_deployment_config(
        workspace_id=workspace_id,
        config_id=config_id,
        member=member,
    )


@router.patch(
    "/workspaces/{workspace_id}/deployment-configs/{config_id}",
    response_model=DeploymentConfigResponse,
    summary="Update deployment configuration",
)
def update_deployment_config(
    workspace_id: uuid.UUID,
    config_id: uuid.UUID,
    payload: DeploymentConfigUpdate,
    db: Session = Depends(get_db),
    member: WorkspaceMember = Depends(RequireWorkspaceRole(MUTATION_ROLES)),
):
    """Updates an existing deployment configuration (ADMIN/OWNER only)."""
    service = DeploymentManagementService(db)
    return service.update_deployment_config(
        workspace_id=workspace_id,
        config_id=config_id,
        data=payload,
        member=member,
    )


@router.delete(
    "/workspaces/{workspace_id}/deployment-configs/{config_id}",
    summary="Delete deployment configuration",
)
def delete_deployment_config(
    workspace_id: uuid.UUID,
    config_id: uuid.UUID,
    db: Session = Depends(get_db),
    member: WorkspaceMember = Depends(RequireWorkspaceRole(MUTATION_ROLES)),
):
    """Deletes a deployment configuration (ADMIN/OWNER only)."""
    service = DeploymentManagementService(db)
    return service.delete_deployment_config(
        workspace_id=workspace_id,
        config_id=config_id,
        member=member,
    )


# --- Deployment Execution API ---

@router.post(
    "/workspaces/{workspace_id}/deployment-configs/{config_id}/deploy",
    response_model=DeploymentResponse,
    summary="Trigger a controlled deployment",
)
async def trigger_deployment(
    workspace_id: uuid.UUID,
    config_id: uuid.UUID,
    payload: DeploymentTriggerRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    member: WorkspaceMember = Depends(RequireWorkspaceRole(MUTATION_ROLES)),
):
    """Triggers a controlled deployment execution on the registered target server (ADMIN/OWNER only)."""
    service = DeploymentManagementService(db)
    return await service.trigger_deployment(
        workspace_id=workspace_id,
        config_id=config_id,
        member=member,
        user_id=current_user.id,
        confirm=payload.confirm,
    )


# --- Deployment History & Logs API ---

@router.get(
    "/workspaces/{workspace_id}/deployments",
    response_model=DeploymentListResponse,
    summary="List deployment history",
)
def list_deployments(
    workspace_id: uuid.UUID,
    environment_id: Optional[uuid.UUID] = Query(None, description="Filter by environment ID"),
    server_id: Optional[uuid.UUID] = Query(None, description="Filter by server ID"),
    deployment_config_id: Optional[uuid.UUID] = Query(None, description="Filter by deployment config ID"),
    status: Optional[str] = Query(None, description="Filter by status (PENDING, RUNNING, SUCCESS, FAILED, CANCELLED)"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    member: WorkspaceMember = Depends(RequireWorkspaceRole(ALL_ROLES)),
):
    """Retrieves paginated deployment history for the workspace."""
    service = DeploymentManagementService(db)
    return service.list_deployments(
        workspace_id=workspace_id,
        member=member,
        environment_id=environment_id,
        server_id=server_id,
        deployment_config_id=deployment_config_id,
        status_filter=status,
        page=page,
        limit=limit,
    )


@router.get(
    "/workspaces/{workspace_id}/deployments/{deployment_id}",
    response_model=DeploymentResponse,
    summary="Get deployment execution details",
)
def get_deployment(
    workspace_id: uuid.UUID,
    deployment_id: uuid.UUID,
    db: Session = Depends(get_db),
    member: WorkspaceMember = Depends(RequireWorkspaceRole(ALL_ROLES)),
):
    """Retrieves details of a specific deployment execution."""
    service = DeploymentManagementService(db)
    return service.get_deployment(
        workspace_id=workspace_id,
        deployment_id=deployment_id,
        member=member,
    )


@router.get(
    "/workspaces/{workspace_id}/deployments/{deployment_id}/logs",
    response_model=DeploymentLogsResponse,
    summary="Get deployment logs",
)
def get_deployment_logs(
    workspace_id: uuid.UUID,
    deployment_id: uuid.UUID,
    lines: int = Query(100, ge=10, le=1000, description="Number of log lines to retrieve"),
    db: Session = Depends(get_db),
    member: WorkspaceMember = Depends(RequireWorkspaceRole(ALL_ROLES)),
):
    """Retrieves logs of a specific deployment execution."""
    service = DeploymentManagementService(db)
    return service.get_deployment_logs(
        workspace_id=workspace_id,
        deployment_id=deployment_id,
        member=member,
        lines=lines,
    )

