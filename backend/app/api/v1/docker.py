import uuid
from typing import Annotated, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import RequireWorkspaceRole
from app.core.validation import validate_safe_identifier
from app.models.workspace_member import WorkspaceMember, WorkspaceRole
from app.schemas.audit_log import AuditAction, AuditStatus
from app.schemas.docker import (
    ContainerFilterState,
    DockerComposeActionRequest,
    DockerComposeActionResult,
    DockerComposeProjectCreate,
    DockerComposeProjectResponse,
    DockerComposeProjectUpdate,
    DockerComposeStatusResponse,
    DockerContainerActionRequest,
    DockerContainerActionResult,
    DockerContainerDetail,
    DockerContainerListResponse,
    DockerContainerLogsResponse,
    DockerStatusResponse,
)
from app.services.audit_service import AuditService
from app.services.docker_management import DockerManagementService

router = APIRouter(
    prefix="/workspaces/{workspace_id}/servers/{server_id}/docker",
    tags=["Docker"],
)

_docker_service_instance: Optional[DockerManagementService] = None


def get_docker_management_service() -> DockerManagementService:
    global _docker_service_instance
    if _docker_service_instance is None:
        _docker_service_instance = DockerManagementService()
    return _docker_service_instance


# 1. Docker Status Detection
@router.get(
    "",
    response_model=DockerStatusResponse,
    summary="Deteksi Status Docker & Docker Daemon",
)
async def get_docker_status(
    workspace_id: uuid.UUID,
    server_id: uuid.UUID,
    member: Annotated[
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
    db: Session = Depends(get_db),
    docker_svc: DockerManagementService = Depends(get_docker_management_service),
):
    role = WorkspaceRole(member.role) if isinstance(member.role, str) else member.role
    return await docker_svc.get_docker_status(db, workspace_id, server_id, member.user_id, role)


# 2. List Containers
@router.get(
    "/containers",
    response_model=DockerContainerListResponse,
    summary="Daftar Container Docker",
)
async def list_containers(
    workspace_id: uuid.UUID,
    server_id: uuid.UUID,
    member: Annotated[
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
    state: ContainerFilterState = Query(
        ContainerFilterState.RUNNING,
        description="Filter container: running (default), stopped, all",
    ),
    db: Session = Depends(get_db),
    docker_svc: DockerManagementService = Depends(get_docker_management_service),
):
    role = WorkspaceRole(member.role) if isinstance(member.role, str) else member.role
    return await docker_svc.list_containers(
        db, workspace_id, server_id, member.user_id, role, state_filter=state
    )


# 3. Get Container Detail
@router.get(
    "/containers/{container_id}",
    response_model=DockerContainerDetail,
    summary="Detail Container Docker",
)
async def get_container_detail(
    workspace_id: uuid.UUID,
    server_id: uuid.UUID,
    container_id: str,
    member: Annotated[
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
    db: Session = Depends(get_db),
    docker_svc: DockerManagementService = Depends(get_docker_management_service),
):
    validate_safe_identifier(container_id, "container_id")
    role = WorkspaceRole(member.role) if isinstance(member.role, str) else member.role
    return await docker_svc.get_container_detail(
        db, workspace_id, server_id, container_id, member.user_id, role
    )


# 4. Start Container
@router.post(
    "/containers/{container_id}/start",
    response_model=DockerContainerActionResult,
    summary="Start Container Docker",
)
async def start_container(
    workspace_id: uuid.UUID,
    server_id: uuid.UUID,
    container_id: str,
    payload: DockerContainerActionRequest,
    request: Request,
    member: Annotated[
        WorkspaceMember,
        Depends(
            RequireWorkspaceRole(
                [
                    WorkspaceRole.OWNER,
                    WorkspaceRole.ADMIN,
                ]
            )
        ),
    ],
    db: Session = Depends(get_db),
    docker_svc: DockerManagementService = Depends(get_docker_management_service),
):
    validate_safe_identifier(container_id, "container_id")
    role = WorkspaceRole(member.role) if isinstance(member.role, str) else member.role
    res = await docker_svc.execute_container_action(
        db, workspace_id, server_id, container_id, "start", payload.confirm, member.user_id, role
    )
    audit = AuditService(db)
    audit.log(
        action=AuditAction.DOCKER_CONTAINER_STARTED,
        resource_type="docker_container",
        status=AuditStatus.SUCCESS if res.success else AuditStatus.FAILED,
        workspace_id=workspace_id,
        user_id=member.user_id,
        resource_id=container_id,
        server_id=server_id,
        metadata={"container_id": container_id, "container": res.container, "success": res.success},
        request=request,
    )
    return res


# 5. Stop Container
@router.post(
    "/containers/{container_id}/stop",
    response_model=DockerContainerActionResult,
    summary="Stop Container Docker",
)
async def stop_container(
    workspace_id: uuid.UUID,
    server_id: uuid.UUID,
    container_id: str,
    payload: DockerContainerActionRequest,
    request: Request,
    member: Annotated[
        WorkspaceMember,
        Depends(
            RequireWorkspaceRole(
                [
                    WorkspaceRole.OWNER,
                    WorkspaceRole.ADMIN,
                ]
            )
        ),
    ],
    db: Session = Depends(get_db),
    docker_svc: DockerManagementService = Depends(get_docker_management_service),
):
    validate_safe_identifier(container_id, "container_id")
    role = WorkspaceRole(member.role) if isinstance(member.role, str) else member.role
    res = await docker_svc.execute_container_action(
        db, workspace_id, server_id, container_id, "stop", payload.confirm, member.user_id, role
    )
    audit = AuditService(db)
    audit.log(
        action=AuditAction.DOCKER_CONTAINER_STOPPED,
        resource_type="docker_container",
        status=AuditStatus.SUCCESS if res.success else AuditStatus.FAILED,
        workspace_id=workspace_id,
        user_id=member.user_id,
        resource_id=container_id,
        server_id=server_id,
        metadata={"container_id": container_id, "container": res.container, "success": res.success},
        request=request,
    )
    return res


# 6. Restart Container
@router.post(
    "/containers/{container_id}/restart",
    response_model=DockerContainerActionResult,
    summary="Restart Container Docker",
)
async def restart_container(
    workspace_id: uuid.UUID,
    server_id: uuid.UUID,
    container_id: str,
    payload: DockerContainerActionRequest,
    request: Request,
    member: Annotated[
        WorkspaceMember,
        Depends(
            RequireWorkspaceRole(
                [
                    WorkspaceRole.OWNER,
                    WorkspaceRole.ADMIN,
                ]
            )
        ),
    ],
    db: Session = Depends(get_db),
    docker_svc: DockerManagementService = Depends(get_docker_management_service),
):
    validate_safe_identifier(container_id, "container_id")
    role = WorkspaceRole(member.role) if isinstance(member.role, str) else member.role
    res = await docker_svc.execute_container_action(
        db, workspace_id, server_id, container_id, "restart", payload.confirm, member.user_id, role
    )
    audit = AuditService(db)
    audit.log(
        action=AuditAction.DOCKER_CONTAINER_RESTARTED,
        resource_type="docker_container",
        status=AuditStatus.SUCCESS if res.success else AuditStatus.FAILED,
        workspace_id=workspace_id,
        user_id=member.user_id,
        resource_id=container_id,
        server_id=server_id,
        metadata={"container_id": container_id, "container": res.container, "success": res.success},
        request=request,
    )
    return res


# 7. Get Container Logs
@router.get(
    "/containers/{container_id}/logs",
    response_model=DockerContainerLogsResponse,
    summary="Ambil Log Container Docker",
)
async def get_container_logs(
    workspace_id: uuid.UUID,
    server_id: uuid.UUID,
    container_id: str,
    member: Annotated[
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
    lines: int = Query(100, ge=10, le=1000, description="Jumlah baris log (10 - 1000)"),
    since: Optional[str] = Query(
        None,
        pattern="^(5m|10m|30m|1h|6h|12h|24h)$",
        description="Filter rentang waktu: 5m, 10m, 30m, 1h, 6h, 12h, 24h",
    ),
    db: Session = Depends(get_db),
    docker_svc: DockerManagementService = Depends(get_docker_management_service),
):
    role = WorkspaceRole(member.role) if isinstance(member.role, str) else member.role
    return await docker_svc.get_container_logs(
        db, workspace_id, server_id, container_id, member.user_id, role, lines=lines, since=since
    )


# 8. List Docker Compose Projects
@router.get(
    "/compose/projects",
    response_model=List[DockerComposeProjectResponse],
    summary="Daftar Docker Compose Project Terdaftar",
)
def list_compose_projects(
    workspace_id: uuid.UUID,
    server_id: uuid.UUID,
    member: Annotated[
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
    db: Session = Depends(get_db),
    docker_svc: DockerManagementService = Depends(get_docker_management_service),
):
    role = WorkspaceRole(member.role) if isinstance(member.role, str) else member.role
    return docker_svc.list_compose_projects(db, workspace_id, server_id, member.user_id, role)


# 9. Create Docker Compose Project
@router.post(
    "/compose/projects",
    response_model=DockerComposeProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrasi Docker Compose Project Baru",
)
def create_compose_project(
    workspace_id: uuid.UUID,
    server_id: uuid.UUID,
    payload: DockerComposeProjectCreate,
    member: Annotated[
        WorkspaceMember,
        Depends(
            RequireWorkspaceRole(
                [
                    WorkspaceRole.OWNER,
                    WorkspaceRole.ADMIN,
                ]
            )
        ),
    ],
    db: Session = Depends(get_db),
    docker_svc: DockerManagementService = Depends(get_docker_management_service),
):
    role = WorkspaceRole(member.role) if isinstance(member.role, str) else member.role
    return docker_svc.create_compose_project(
        db, workspace_id, server_id, member.user_id, role, payload
    )


# 10. Get Docker Compose Project
@router.get(
    "/compose/projects/{project_id}",
    response_model=DockerComposeProjectResponse,
    summary="Detail Konfigurasi Docker Compose Project",
)
def get_compose_project(
    workspace_id: uuid.UUID,
    server_id: uuid.UUID,
    project_id: uuid.UUID,
    member: Annotated[
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
    db: Session = Depends(get_db),
    docker_svc: DockerManagementService = Depends(get_docker_management_service),
):
    role = WorkspaceRole(member.role) if isinstance(member.role, str) else member.role
    return docker_svc.get_compose_project(
        db, workspace_id, server_id, project_id, member.user_id, role
    )


# 11. Update Docker Compose Project
@router.patch(
    "/compose/projects/{project_id}",
    response_model=DockerComposeProjectResponse,
    summary="Update Konfigurasi Docker Compose Project",
)
def update_compose_project(
    workspace_id: uuid.UUID,
    server_id: uuid.UUID,
    project_id: uuid.UUID,
    payload: DockerComposeProjectUpdate,
    member: Annotated[
        WorkspaceMember,
        Depends(
            RequireWorkspaceRole(
                [
                    WorkspaceRole.OWNER,
                    WorkspaceRole.ADMIN,
                ]
            )
        ),
    ],
    db: Session = Depends(get_db),
    docker_svc: DockerManagementService = Depends(get_docker_management_service),
):
    role = WorkspaceRole(member.role) if isinstance(member.role, str) else member.role
    return docker_svc.update_compose_project(
        db, workspace_id, server_id, project_id, member.user_id, role, payload
    )


# 12. Delete Docker Compose Project
@router.delete(
    "/compose/projects/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Hapus Registrasi Docker Compose Project",
)
def delete_compose_project(
    workspace_id: uuid.UUID,
    server_id: uuid.UUID,
    project_id: uuid.UUID,
    member: Annotated[
        WorkspaceMember,
        Depends(
            RequireWorkspaceRole(
                [
                    WorkspaceRole.OWNER,
                    WorkspaceRole.ADMIN,
                ]
            )
        ),
    ],
    db: Session = Depends(get_db),
    docker_svc: DockerManagementService = Depends(get_docker_management_service),
):
    role = WorkspaceRole(member.role) if isinstance(member.role, str) else member.role
    docker_svc.delete_compose_project(
        db, workspace_id, server_id, project_id, member.user_id, role
    )


# 13. Get Compose Project Runtime Status
@router.get(
    "/compose/projects/{project_id}/status",
    response_model=DockerComposeStatusResponse,
    summary="Status Runtime Layanan Docker Compose",
)
async def get_compose_status(
    workspace_id: uuid.UUID,
    server_id: uuid.UUID,
    project_id: uuid.UUID,
    member: Annotated[
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
    db: Session = Depends(get_db),
    docker_svc: DockerManagementService = Depends(get_docker_management_service),
):
    role = WorkspaceRole(member.role) if isinstance(member.role, str) else member.role
    return await docker_svc.get_compose_status(
        db, workspace_id, server_id, project_id, member.user_id, role
    )


# 14. Compose Up
@router.post(
    "/compose/projects/{project_id}/up",
    response_model=DockerComposeActionResult,
    summary="Jalankan Docker Compose Up",
)
async def compose_up(
    workspace_id: uuid.UUID,
    server_id: uuid.UUID,
    project_id: uuid.UUID,
    payload: DockerComposeActionRequest,
    request: Request,
    member: Annotated[
        WorkspaceMember,
        Depends(
            RequireWorkspaceRole(
                [
                    WorkspaceRole.OWNER,
                    WorkspaceRole.ADMIN,
                ]
            )
        ),
    ],
    db: Session = Depends(get_db),
    docker_svc: DockerManagementService = Depends(get_docker_management_service),
):
    role = WorkspaceRole(member.role) if isinstance(member.role, str) else member.role
    res = await docker_svc.execute_compose_action(
        db, workspace_id, server_id, project_id, "up", payload.confirm, member.user_id, role
    )
    audit = AuditService(db)
    audit.log(
        action=AuditAction.DOCKER_COMPOSE_STARTED,
        resource_type="docker_compose",
        status=AuditStatus.SUCCESS if res.success else AuditStatus.FAILED,
        workspace_id=workspace_id,
        user_id=member.user_id,
        resource_id=str(project_id),
        server_id=server_id,
        metadata={"project_id": str(project_id), "action": "up", "success": res.success},
        request=request,
    )
    return res


# 15. Compose Down
@router.post(
    "/compose/projects/{project_id}/down",
    response_model=DockerComposeActionResult,
    summary="Jalankan Docker Compose Down",
)
async def compose_down(
    workspace_id: uuid.UUID,
    server_id: uuid.UUID,
    project_id: uuid.UUID,
    payload: DockerComposeActionRequest,
    request: Request,
    member: Annotated[
        WorkspaceMember,
        Depends(
            RequireWorkspaceRole(
                [
                    WorkspaceRole.OWNER,
                    WorkspaceRole.ADMIN,
                ]
            )
        ),
    ],
    db: Session = Depends(get_db),
    docker_svc: DockerManagementService = Depends(get_docker_management_service),
):
    role = WorkspaceRole(member.role) if isinstance(member.role, str) else member.role
    res = await docker_svc.execute_compose_action(
        db, workspace_id, server_id, project_id, "down", payload.confirm, member.user_id, role
    )
    audit = AuditService(db)
    audit.log(
        action=AuditAction.DOCKER_COMPOSE_STOPPED,
        resource_type="docker_compose",
        status=AuditStatus.SUCCESS if res.success else AuditStatus.FAILED,
        workspace_id=workspace_id,
        user_id=member.user_id,
        resource_id=str(project_id),
        server_id=server_id,
        metadata={"project_id": str(project_id), "action": "down", "success": res.success},
        request=request,
    )
    return res


# 16. Compose Restart
@router.post(
    "/compose/projects/{project_id}/restart",
    response_model=DockerComposeActionResult,
    summary="Jalankan Docker Compose Restart",
)
async def compose_restart(
    workspace_id: uuid.UUID,
    server_id: uuid.UUID,
    project_id: uuid.UUID,
    payload: DockerComposeActionRequest,
    request: Request,
    member: Annotated[
        WorkspaceMember,
        Depends(
            RequireWorkspaceRole(
                [
                    WorkspaceRole.OWNER,
                    WorkspaceRole.ADMIN,
                ]
            )
        ),
    ],
    db: Session = Depends(get_db),
    docker_svc: DockerManagementService = Depends(get_docker_management_service),
):
    role = WorkspaceRole(member.role) if isinstance(member.role, str) else member.role
    res = await docker_svc.execute_compose_action(
        db, workspace_id, server_id, project_id, "restart", payload.confirm, member.user_id, role
    )
    audit = AuditService(db)
    audit.log(
        action=AuditAction.DOCKER_COMPOSE_RESTARTED,
        resource_type="docker_compose",
        status=AuditStatus.SUCCESS if res.success else AuditStatus.FAILED,
        workspace_id=workspace_id,
        user_id=member.user_id,
        resource_id=str(project_id),
        server_id=server_id,
        metadata={"project_id": str(project_id), "action": "restart", "success": res.success},
        request=request,
    )
    return res
