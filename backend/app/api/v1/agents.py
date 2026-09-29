import uuid
from datetime import datetime, timezone
from typing import Annotated, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, WebSocket, WebSocketDisconnect, status
from sqlalchemy.orm import Session
from sqlalchemy import select, desc

from app.core.database import get_db
from app.core.deps import RequireWorkspaceRole
from app.models.agent import Agent, AgentJob
from app.models.server import Server
from app.models.workspace_member import WorkspaceMember, WorkspaceRole
from app.schemas.agent import (
    AgentEnrollmentRequest,
    AgentEnrollmentResponse,
    AgentHeartbeatRequest,
    AgentHeartbeatResponse,
    AgentJobResponse,
    AgentRegisterRequest,
    AgentRegisterResponse,
    AgentResponse,
)
from app.schemas.audit_log import AuditAction, AuditStatus
from app.services.agent_dispatcher import dispatcher_instance
from app.services.agent_manager import AgentManager
from app.services.audit_service import AuditService

router = APIRouter(tags=["DevOps Agent"])


# ==========================================
# 1. Management Endpoints (Called by Flutter / Admin)
# ==========================================

@router.post(
    "/workspaces/{workspace_id}/servers/{server_id}/agent/enrollment",
    response_model=AgentEnrollmentResponse,
    summary="Generate One-Time Agent Enrollment Token",
)
def create_enrollment_token(
    workspace_id: uuid.UUID,
    server_id: uuid.UUID,
    request: Request,
    membership: Annotated[
        WorkspaceMember,
        Depends(RequireWorkspaceRole([WorkspaceRole.OWNER, WorkspaceRole.ADMIN])),
    ],
    payload: Optional[AgentEnrollmentRequest] = None,
    db: Session = Depends(get_db),
):
    try:
        base_url = str(request.base_url).rstrip("/")
        expires_in = payload.expires_in_minutes if payload else 15
        token_obj, raw_token, installer_cmd = AgentManager.create_enrollment_token(
            db=db,
            workspace_id=workspace_id,
            server_id=server_id,
            user_id=membership.user_id,
            expires_in_minutes=expires_in,
            backend_url=base_url,
        )

        return AgentEnrollmentResponse(
            enrollment_token=raw_token,
            server_id=server_id,
            workspace_id=workspace_id,
            expires_at=token_obj.expires_at,
            installer_command=installer_cmd,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/workspaces/{workspace_id}/servers/{server_id}/agent",
    response_model=AgentResponse,
    summary="Get Agent Status & Details",
)
def get_agent_status(
    workspace_id: uuid.UUID,
    server_id: uuid.UUID,
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
    db: Session = Depends(get_db),
):
    agent = AgentManager.get_agent_for_server(db, workspace_id, server_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent belum terdaftar/enrolled pada server ini.",
        )
    return agent


@router.post(
    "/workspaces/{workspace_id}/servers/{server_id}/agent/disable",
    response_model=AgentResponse,
    summary="Disable Agent",
)
def disable_agent(
    workspace_id: uuid.UUID,
    server_id: uuid.UUID,
    membership: Annotated[
        WorkspaceMember,
        Depends(RequireWorkspaceRole([WorkspaceRole.OWNER, WorkspaceRole.ADMIN])),
    ],
    db: Session = Depends(get_db),
):
    try:
        agent = AgentManager.disable_agent(
            db=db,
            workspace_id=workspace_id,
            server_id=server_id,
            user_id=membership.user_id,
        )
        return agent
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/workspaces/{workspace_id}/servers/{server_id}/agent/revoke",
    response_model=AgentResponse,
    summary="Revoke Agent Credentials & Reset to SSH",
)
def revoke_agent(
    workspace_id: uuid.UUID,
    server_id: uuid.UUID,
    membership: Annotated[
        WorkspaceMember,
        Depends(RequireWorkspaceRole([WorkspaceRole.OWNER, WorkspaceRole.ADMIN])),
    ],
    db: Session = Depends(get_db),
):
    try:
        agent = AgentManager.revoke_agent(
            db=db,
            workspace_id=workspace_id,
            server_id=server_id,
            user_id=membership.user_id,
        )
        return agent
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/workspaces/{workspace_id}/servers/{server_id}/agent/jobs",
    response_model=List[AgentJobResponse],
    summary="Get Agent Job Execution History",
)
def list_agent_jobs(
    workspace_id: uuid.UUID,
    server_id: uuid.UUID,
    membership: Annotated[
        WorkspaceMember,
        Depends(
            RequireWorkspaceRole(
                [
                    WorkspaceRole.OWNER,
                    WorkspaceRole.ADMIN,
                    WorkspaceRole.DEVELOPER,
                ]
            )
        ),
    ],
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    jobs = (
        db.query(AgentJob)
        .filter(
            AgentJob.workspace_id == workspace_id,
            AgentJob.server_id == server_id,
        )
        .order_by(desc(AgentJob.created_at))
        .limit(limit)
        .all()
    )
    return jobs


# ==========================================
# 2. Outbound Agent Handshake & Transport Endpoints
# ==========================================

@router.post(
    "/agent/enroll",
    response_model=AgentRegisterResponse,
    summary="Agent Enrollment Handshake",
)
def enroll_agent(
    payload: AgentRegisterRequest,
    db: Session = Depends(get_db),
):
    try:
        agent, agent_token = AgentManager.enroll_agent(
            db=db,
            enrollment_token=payload.enrollment_token,
            hostname=payload.hostname,
            operating_system=payload.operating_system,
            architecture=payload.architecture,
            agent_version=payload.agent_version,
            capabilities=payload.capabilities,
        )
        return AgentRegisterResponse(
            agent_id=agent.id,
            server_id=agent.server_id,
            workspace_id=agent.workspace_id,
            agent_token=agent_token,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/agent/heartbeat",
    response_model=AgentHeartbeatResponse,
    summary="Agent Periodic Heartbeat (HTTP Fallback)",
)
def agent_heartbeat(
    payload: AgentHeartbeatRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    agent_token = request.headers.get("X-Agent-Token")
    if not agent_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing X-Agent-Token header.")

    agent = AgentManager.authenticate_agent(db, payload.agent_id, agent_token)
    if not agent:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Agent credentials or agent disabled.")

    AgentManager.heartbeat(
        db=db,
        agent_id=agent.id,
        agent_version=payload.agent_version,
        hostname=payload.hostname,
        operating_system=payload.operating_system,
        architecture=payload.architecture,
        capabilities=payload.capabilities,
        status=payload.status,
    )

    return AgentHeartbeatResponse(acknowledged=True, server_time=datetime.now(timezone.utc))


@router.websocket("/agent/ws")
async def agent_websocket(
    websocket: WebSocket,
    agent_id: Optional[str] = Query(None),
    agent_token: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    await websocket.accept()

    if not agent_id or not agent_token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Missing agent credentials")
        return

    try:
        agent_uuid = uuid.UUID(agent_id)
    except ValueError:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid agent_id UUID")
        return

    agent = AgentManager.authenticate_agent(db, agent_uuid, agent_token)
    if not agent:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Agent authentication failed")
        return

    # Update agent state
    agent.status = "ONLINE"
    agent.connected_at = datetime.now(timezone.utc)
    agent.last_seen_at = datetime.now(timezone.utc)
    db.commit()

    # Register in memory dispatcher
    await dispatcher_instance.register_connection(agent.id, websocket)

    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")

            if msg_type == "HEARTBEAT":
                AgentManager.heartbeat(
                    db=db,
                    agent_id=agent.id,
                    agent_version=data.get("agent_version", "1.0.0"),
                    hostname=data.get("hostname"),
                    operating_system=data.get("operating_system"),
                    architecture=data.get("architecture"),
                    capabilities=data.get("capabilities"),
                    status="ONLINE",
                )
                await websocket.send_json({
                    "type": "HEARTBEAT_ACK",
                    "server_time": datetime.now(timezone.utc).isoformat(),
                })
            elif msg_type == "JOB_RESULT":
                await dispatcher_instance.handle_agent_message(agent.id, data)

    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        await dispatcher_instance.unregister_connection(agent.id, websocket)
        agent.disconnected_at = datetime.now(timezone.utc)
        db.commit()
