import uuid
from typing import Annotated, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import RequireWorkspaceRole
from app.models.user import User
from app.models.workspace_member import WorkspaceRole
from app.models.environment import Environment
from app.models.server import Server
from app.models.server_credential import ServerCredential
from app.schemas.server import (
    ServerCreate,
    ServerUpdate,
    ServerResponse,
    EnvironmentSummary,
    ConnectionTestResponse,
)
from app.services.encryption import secret_encryption_service
from app.services.connection_provider import get_connection_provider

router = APIRouter(
    prefix="/workspaces/{workspace_id}/servers",
    tags=["Servers"],
)


def _to_server_response(server: Server) -> ServerResponse:
    has_cred = server.credential is not None
    auth_type = server.credential.auth_type if server.credential else None
    env_summary = (
        EnvironmentSummary(
            id=server.environment.id,
            name=server.environment.name,
            key=server.environment.key,
        )
        if server.environment
        else None
    )

    return ServerResponse(
        id=server.id,
        workspace_id=server.workspace_id,
        environment_id=server.environment_id,
        name=server.name,
        hostname=server.hostname,
        ip_address=server.ip_address,
        ssh_port=server.ssh_port,
        username=server.username,
        operating_system=server.operating_system,
        description=server.description,
        is_active=server.is_active,
        environment=env_summary,
        has_credential=has_cred,
        auth_type=auth_type,
        status="UNKNOWN",
        created_at=server.created_at,
        updated_at=server.updated_at,
    )


@router.get(
    "",
    response_model=List[ServerResponse],
    summary="Daftar Server dalam Workspace",
)
def list_servers(
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
    environment_id: Optional[uuid.UUID] = Query(None, description="Filter berdasarkan environment"),
):
    """Mengambil daftar seluruh server dalam workspace, opsional difilter berdasarkan environment."""
    query = db.query(Server).filter(Server.workspace_id == workspace_id)
    if environment_id:
        query = query.filter(Server.environment_id == environment_id)

    servers = query.order_by(Server.created_at.asc()).all()
    return [_to_server_response(s) for s in servers]


@router.post(
    "",
    response_model=ServerResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Tambah Server Baru (OWNER, ADMIN)",
)
def create_server(
    workspace_id: uuid.UUID,
    data: ServerCreate,
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
    """Menambahkan server baru ke workspace.

    Environment wajib berada di dalam workspace yang sama. Credential dienkripsi.
    """
    # 1. Validasi environment berada di workspace yang sama
    env = (
        db.query(Environment)
        .filter(
            Environment.id == data.environment_id,
            Environment.workspace_id == workspace_id,
        )
        .first()
    )
    if not env:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Environment tidak valid atau tidak berada dalam workspace ini.",
        )

    # 2. Buat instance server
    server = Server(
        workspace_id=workspace_id,
        environment_id=data.environment_id,
        name=data.name.strip(),
        hostname=data.hostname.strip() if data.hostname else None,
        ip_address=data.ip_address.strip() if data.ip_address else None,
        ssh_port=data.ssh_port,
        username=data.username.strip() if data.username else None,
        operating_system=data.operating_system.strip() if data.operating_system else None,
        description=data.description.strip() if data.description else None,
        is_active=data.is_active,
    )
    db.add(server)
    db.flush()

    # 3. Handle credential jika disertakan
    if data.credential:
        cred = ServerCredential(
            server_id=server.id,
            auth_type=data.credential.auth_type,
            username=data.credential.username.strip(),
            encrypted_password=secret_encryption_service.encrypt(data.credential.password),
            encrypted_private_key=secret_encryption_service.encrypt(data.credential.private_key),
            encrypted_passphrase=secret_encryption_service.encrypt(data.credential.passphrase),
        )
        db.add(cred)
        # update default server username if not specified
        if not server.username:
            server.username = data.credential.username.strip()

    db.commit()
    db.refresh(server)
    return _to_server_response(server)


@router.get(
    "/{server_id}",
    response_model=ServerResponse,
    summary="Detail Server",
)
def get_server(
    workspace_id: uuid.UUID,
    server_id: uuid.UUID,
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
    """Mengambil detail server dalam workspace."""
    server = (
        db.query(Server)
        .filter(
            Server.id == server_id,
            Server.workspace_id == workspace_id,
        )
        .first()
    )
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server tidak ditemukan dalam workspace ini.",
        )

    return _to_server_response(server)


@router.patch(
    "/{server_id}",
    response_model=ServerResponse,
    summary="Update Server (OWNER, ADMIN)",
)
def update_server(
    workspace_id: uuid.UUID,
    server_id: uuid.UUID,
    data: ServerUpdate,
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
    """Mengubah data server atau credential."""
    server = (
        db.query(Server)
        .filter(
            Server.id == server_id,
            Server.workspace_id == workspace_id,
        )
        .first()
    )
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server tidak ditemukan dalam workspace ini.",
        )

    if data.environment_id is not None:
        env = (
            db.query(Environment)
            .filter(
                Environment.id == data.environment_id,
                Environment.workspace_id == workspace_id,
            )
            .first()
        )
        if not env:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Environment tidak valid atau tidak berada dalam workspace ini.",
            )
        server.environment_id = data.environment_id

    if data.name is not None:
        server.name = data.name.strip()
    if data.hostname is not None:
        server.hostname = data.hostname.strip() if data.hostname else None
    if data.ip_address is not None:
        server.ip_address = data.ip_address.strip() if data.ip_address else None
    if data.ssh_port is not None:
        server.ssh_port = data.ssh_port
    if data.username is not None:
        server.username = data.username.strip() if data.username else None
    if data.operating_system is not None:
        server.operating_system = data.operating_system.strip() if data.operating_system else None
    if data.description is not None:
        server.description = data.description.strip() if data.description else None
    if data.is_active is not None:
        server.is_active = data.is_active

    if data.credential is not None:
        if server.credential:
            server.credential.auth_type = data.credential.auth_type
            server.credential.username = data.credential.username.strip()
            if data.credential.password is not None:
                server.credential.encrypted_password = secret_encryption_service.encrypt(data.credential.password)
            if data.credential.private_key is not None:
                server.credential.encrypted_private_key = secret_encryption_service.encrypt(data.credential.private_key)
            if data.credential.passphrase is not None:
                server.credential.encrypted_passphrase = secret_encryption_service.encrypt(data.credential.passphrase)
        else:
            cred = ServerCredential(
                server_id=server.id,
                auth_type=data.credential.auth_type,
                username=data.credential.username.strip(),
                encrypted_password=secret_encryption_service.encrypt(data.credential.password),
                encrypted_private_key=secret_encryption_service.encrypt(data.credential.private_key),
                encrypted_passphrase=secret_encryption_service.encrypt(data.credential.passphrase),
            )
            db.add(cred)

    db.commit()
    db.refresh(server)
    return _to_server_response(server)


@router.delete(
    "/{server_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Hapus Server (OWNER, ADMIN)",
)
def delete_server(
    workspace_id: uuid.UUID,
    server_id: uuid.UUID,
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
    """Menghapus server beserta credential terkait."""
    server = (
        db.query(Server)
        .filter(
            Server.id == server_id,
            Server.workspace_id == workspace_id,
        )
        .first()
    )
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server tidak ditemukan dalam workspace ini.",
        )

    db.delete(server)
    db.commit()
    return None


@router.post(
    "/{server_id}/connection-test",
    response_model=ConnectionTestResponse,
    summary="Test Koneksi SSH Server (OWNER, ADMIN, DEVELOPER)",
)
async def test_server_connection(
    workspace_id: uuid.UUID,
    server_id: uuid.UUID,
    auth: Annotated[
        tuple[User, WorkspaceRole],
        Depends(
            RequireWorkspaceRole([
                WorkspaceRole.OWNER,
                WorkspaceRole.ADMIN,
                WorkspaceRole.DEVELOPER,
            ])
        ),
    ],
    db: Annotated[Session, Depends(get_db)],
):
    """Melakukan pengujian koneksi SSH ke remote server secara asynchronous.

    Mendekripsi credential di memory, menjalankan sanity check lightweight, dan mengembalikan status koneksi.
    """
    server = (
        db.query(Server)
        .filter(
            Server.id == server_id,
            Server.workspace_id == workspace_id,
        )
        .first()
    )
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server tidak ditemukan dalam workspace ini.",
        )

    target_host = server.ip_address or server.hostname
    if not target_host:
        return ConnectionTestResponse(
            success=False,
            message="Server tidak memiliki IP Address atau Hostname yang valid.",
            status="OFFLINE",
        )

    if not server.credential:
        return ConnectionTestResponse(
            success=False,
            message="Server belum memiliki credential SSH tersimpan.",
            status="OFFLINE",
        )

    # Decrypt credentials in-memory for the duration of the test
    plain_password = secret_encryption_service.decrypt(server.credential.encrypted_password)
    plain_private_key = secret_encryption_service.decrypt(server.credential.encrypted_private_key)
    plain_passphrase = secret_encryption_service.decrypt(server.credential.encrypted_passphrase)
    username = server.credential.username or server.username or "root"

    provider = get_connection_provider()
    result = await provider.test_connection(
        host=target_host,
        port=server.ssh_port,
        username=username,
        password=plain_password,
        private_key=plain_private_key,
        passphrase=plain_passphrase,
    )

    return ConnectionTestResponse(
        success=result.success,
        message=result.message,
        status=result.status,
        server_info=result.server_info,
    )
