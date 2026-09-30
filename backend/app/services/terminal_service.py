import asyncio
import json
import logging
import uuid
from typing import Optional, Tuple
import asyncssh
from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.server import Server
from app.models.user import User
from app.services.encryption import secret_encryption_service
from app.services.audit_service import AuditService

logger = logging.getLogger(__name__)


class TerminalService:
    def __init__(self, db: Session):
        self.db = db
        self.audit_service = AuditService(db)

    async def handle_ssh_terminal(
        self,
        websocket: WebSocket,
        server: Server,
        user: User,
        initial_cols: int = 80,
        initial_rows: int = 24,
    ) -> None:
        """
        Manages an interactive PTY terminal session over WebSocket using asyncssh.
        """
        host = server.ip_address or server.hostname
        port = server.ssh_port or 22
        username = server.username or "root"

        if not host or not username:
            await websocket.send_text(
                "\r\n\x1b[31;1m[DevOpsHub] Error: Server host or username is not configured.\x1b[0m\r\n"
            )
            await websocket.close(code=1011, reason="Server host or username missing")
            return

        # Decrypt credentials
        password = None
        private_key = None
        passphrase = None
        client_keys = None

        if server.credential:
            if server.credential.encrypted_password:
                try:
                    password = secret_encryption_service.decrypt(
                        server.credential.encrypted_password
                    )
                except Exception as e:
                    logger.error("Failed to decrypt SSH password: %s", e)

            if server.credential.encrypted_private_key:
                try:
                    private_key = secret_encryption_service.decrypt(
                        server.credential.encrypted_private_key
                    )
                except Exception as e:
                    logger.error("Failed to decrypt SSH private key: %s", e)

            if server.credential.encrypted_passphrase:
                try:
                    passphrase = secret_encryption_service.decrypt(
                        server.credential.encrypted_passphrase
                    )
                except Exception as e:
                    logger.error("Failed to decrypt SSH passphrase: %s", e)

        if private_key:
            try:
                client_keys = [
                    asyncssh.import_private_key(private_key, passphrase=passphrase)
                ]
            except Exception as e:
                logger.error("Failed to import SSH private key: %s", e)
                await websocket.send_text(
                    f"\r\n\x1b[31;1m[DevOpsHub] Error: Format SSH private key tidak valid ({e}).\x1b[0m\r\n"
                )
                await websocket.close(code=1011, reason="Invalid SSH key")
                return

        # Log audit trail for session start
        try:
            self.audit_service.log(
                action="TERMINAL_SESSION_OPENED",
                resource_type="server",
                status="SUCCESS",
                workspace_id=server.workspace_id,
                user_id=user.id,
                resource_id=str(server.id),
                server_id=server.id,
                ip_address=websocket.client.host if websocket.client else None,
                user_agent="DevOpsHub-Mobile-Terminal",
                metadata={
                    "server_id": str(server.id),
                    "server_name": server.name,
                    "host": host,
                    "port": port,
                    "user": username,
                },
            )
        except Exception as err:
            logger.warning("Failed to record audit log for terminal open: %s", err)

        await websocket.send_text(
            f"\x1b[36;1m[DevOpsHub] Menghubungkan ke {username}@{host}:{port} via PTY...\x1b[0m\r\n"
        )

        try:
            async with asyncssh.connect(
                host=host,
                port=port,
                username=username,
                password=password,
                client_keys=client_keys,
                known_hosts=None,
                login_timeout=15,
            ) as conn:
                await websocket.send_text(
                    f"\x1b[32;1m[DevOpsHub] Koneksi SSH PTY berhasil terhubung! (xterm-256color)\x1b[0m\r\n\r\n"
                )

                # Create interactive process
                process = await conn.create_process(
                    term_type="xterm-256color",
                    term_size=(initial_cols, initial_rows),
                    encoding=None,  # Binary mode for raw terminal bytes
                )

                async def forward_stdout():
                    try:
                        while not process.stdout.at_eof():
                            data = await process.stdout.read(4096)
                            if not data:
                                break
                            # Forward raw bytes decoded as UTF-8 with replacement
                            await websocket.send_text(
                                data.decode("utf-8", errors="replace")
                            )
                    except asyncio.CancelledError:
                        pass
                    except Exception as stdout_err:
                        logger.debug("stdout stream closed: %s", stdout_err)

                async def forward_stderr():
                    try:
                        while not process.stderr.at_eof():
                            data = await process.stderr.read(4096)
                            if not data:
                                break
                            await websocket.send_text(
                                data.decode("utf-8", errors="replace")
                            )
                    except asyncio.CancelledError:
                        pass
                    except Exception as stderr_err:
                        logger.debug("stderr stream closed: %s", stderr_err)

                async def forward_stdin():
                    try:
                        while True:
                            msg = await websocket.receive_text()
                            # Check if message is a JSON control command (e.g. resize)
                            if msg.startswith("{") and "type" in msg:
                                try:
                                    payload = json.loads(msg)
                                    msg_type = payload.get("type")
                                    if msg_type == "resize":
                                        new_cols = int(payload.get("cols", 80))
                                        new_rows = int(payload.get("rows", 24))
                                        process.terminal_size = (new_cols, new_rows)
                                        continue
                                    elif msg_type == "stdin":
                                        data_to_send = payload.get("data", "")
                                        process.stdin.write(data_to_send.encode("utf-8"))
                                        await process.stdin.drain()
                                        continue
                                except Exception:
                                    pass

                            # Regular text input / keystroke
                            process.stdin.write(msg.encode("utf-8"))
                            await process.stdin.drain()
                    except WebSocketDisconnect:
                        pass
                    except asyncio.CancelledError:
                        pass
                    except Exception as stdin_err:
                        logger.debug("stdin stream error: %s", stdin_err)

                # Run stdout, stderr, and stdin concurrently
                stdout_task = asyncio.create_task(forward_stdout())
                stderr_task = asyncio.create_task(forward_stderr())
                stdin_task = asyncio.create_task(forward_stdin())

                done, pending = await asyncio.wait(
                    [stdout_task, stderr_task, stdin_task],
                    return_when=asyncio.FIRST_COMPLETED,
                )

                for task in pending:
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass

                process.terminate()

        except asyncssh.PermissionDenied:
            await websocket.send_text(
                "\r\n\x1b[31;1m[DevOpsHub] Gagal autentikasi SSH: Username / Password / Key ditolak oleh server.\x1b[0m\r\n"
            )
        except (OSError, ConnectionRefusedError, asyncssh.Error, asyncio.TimeoutError) as e:
            await websocket.send_text(
                f"\r\n\x1b[31;1m[DevOpsHub] Gagal terhubung ke host {host}:{port}: {e}\x1b[0m\r\n"
            )
        except Exception as e:
            logger.error("Terminal session error: %s", e)
            await websocket.send_text(
                f"\r\n\x1b[31;1m[DevOpsHub] Sesi terminal dihentikan: {e}\x1b[0m\r\n"
            )
        finally:
            try:
                self.audit_service.log(
                    action="TERMINAL_SESSION_CLOSED",
                    resource_type="server",
                    status="SUCCESS",
                    workspace_id=server.workspace_id,
                    user_id=user.id,
                    resource_id=str(server.id),
                    server_id=server.id,
                    ip_address=websocket.client.host if websocket.client else None,
                    user_agent="DevOpsHub-Mobile-Terminal",
                    metadata={
                        "server_id": str(server.id),
                        "server_name": server.name,
                    },
                )
            except Exception as err:
                logger.warning("Failed to record audit log for terminal close: %s", err)
