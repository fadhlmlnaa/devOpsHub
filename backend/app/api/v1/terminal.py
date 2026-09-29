import logging
import uuid
from typing import Annotated, Optional
import jwt
from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect, status
from sqlalchemy.orm import Session

from app.core.database import SessionLocal, get_db
from app.core.deps import RequireWorkspaceRole
from app.core.security import decode_access_token
from app.models.server import Server
from app.models.user import User
from app.models.workspace_member import WorkspaceMember, WorkspaceRole
from app.services.terminal_service import TerminalService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/workspaces/{workspace_id}/servers/{server_id}/terminal",
    tags=["Terminal"],
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
    "/status",
    summary="Cek Status Kesiapan Terminal SSH",
)
def get_terminal_status(
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
                ]
            )
        ),
    ],
    db: Session = Depends(get_db),
):
    server = _get_server_or_404(db, workspace_id, server_id)
    return {
        "server_id": str(server.id),
        "server_name": server.name,
        "host": server.ip_address or server.hostname,
        "port": server.ssh_port or 22,
        "user": server.username,
        "connection_type": server.connection_type.value if hasattr(server.connection_type, "value") else str(server.connection_type),
        "has_credential": server.credential is not None,
        "is_active": server.is_active,
    }


@router.websocket("/ws")
async def terminal_websocket(
    websocket: WebSocket,
    workspace_id: uuid.UUID,
    server_id: uuid.UUID,
    token: Optional[str] = Query(None),
    cols: int = Query(80, ge=20, le=300),
    rows: int = Query(24, ge=5, le=100),
):
    await websocket.accept()

    # Authenticate JWT Token from query param or subprotocol/header
    if not token:
        # Check authorization header if query param not present
        auth_header = websocket.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1]

    if not token:
        await websocket.send_text("\r\n\x1b[31;1m[DevOpsHub] Error: Token autentikasi tidak disertakan.\x1b[0m\r\n")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Missing token")
        return

    db = SessionLocal()
    try:
        try:
            payload = decode_access_token(token)
            if payload.get("type") != "access":
                raise ValueError("Invalid token type")
            user_id = uuid.UUID(payload.get("sub"))
        except Exception as e:
            logger.warning("Terminal WS auth failed: %s", e)
            await websocket.send_text("\r\n\x1b[31;1m[DevOpsHub] Error: Token autentikasi tidak valid atau kedaluwarsa.\x1b[0m\r\n")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token")
            return

        user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
        if not user:
            await websocket.send_text("\r\n\x1b[31;1m[DevOpsHub] Error: Pengguna tidak aktif atau tidak ditemukan.\x1b[0m\r\n")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="User not found")
            return

        # Check membership and RBAC role (OWNER, ADMIN, DEVELOPER)
        membership = (
            db.query(WorkspaceMember)
            .filter(
                WorkspaceMember.workspace_id == workspace_id,
                WorkspaceMember.user_id == user.id,
            )
            .first()
        )
        if not membership or membership.role not in [
            WorkspaceRole.OWNER.value,
            WorkspaceRole.ADMIN.value,
            WorkspaceRole.DEVELOPER.value,
        ]:
            await websocket.send_text(
                "\r\n\x1b[31;1m[DevOpsHub] Error: Anda tidak memiliki izin akses terminal (Role VIEWER dibatasi).\x1b[0m\r\n"
            )
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Forbidden")
            return

        server = (
            db.query(Server)
            .filter(Server.id == server_id, Server.workspace_id == workspace_id)
            .first()
        )
        if not server:
            await websocket.send_text("\r\n\x1b[31;1m[DevOpsHub] Error: Server tidak ditemukan.\x1b[0m\r\n")
            await websocket.close(code=1011, reason="Server not found")
            return

        terminal_svc = TerminalService(db)
        await terminal_svc.handle_ssh_terminal(
            websocket=websocket,
            server=server,
            user=user,
            initial_cols=cols,
            initial_rows=rows,
        )

    except WebSocketDisconnect:
        logger.info("Terminal WebSocket disconnected for server %s", server_id)
    except Exception as e:
        logger.error("Terminal WebSocket error: %s", e)
    finally:
        db.close()
