import asyncio
import logging
import re
from typing import Any, Dict, List, Optional
import asyncssh

from app.core.config import settings
from app.infrastructure.service_providers.base import (
    ServiceActionResult,
    ServiceInfo,
    ServiceListResult,
    ServiceProvider,
)

logger = logging.getLogger(__name__)

ALLOWED_ACTIONS = {"start", "stop", "restart", "reload"}
SERVICE_NAME_PATTERN = re.compile(r"^[A-Za-z0-9_.@:-]+\.service$")


class SSHSystemdProvider(ServiceProvider):
    """Systemd service management provider over SSH."""

    def __init__(
        self,
        connect_timeout: int = settings.SERVICE_CONNECTION_TIMEOUT,
        command_timeout: int = settings.SERVICE_COMMAND_TIMEOUT,
    ):
        self.connect_timeout = connect_timeout
        self.command_timeout = command_timeout

    async def _create_connection(
        self,
        host: str,
        port: int,
        username: str,
        password: Optional[str] = None,
        private_key: Optional[str] = None,
        passphrase: Optional[str] = None,
    ):
        client_keys = None
        if private_key:
            try:
                client_keys = [asyncssh.import_private_key(private_key, passphrase=passphrase)]
            except Exception as e:
                logger.warning("Invalid SSH private key: %s", type(e).__name__)
                raise ValueError("Format SSH private key tidak valid atau passphrase salah.") from e

        return await asyncio.wait_for(
            asyncssh.connect(
                host=host,
                port=port,
                username=username,
                password=password,
                client_keys=client_keys,
                known_hosts=None,
            ),
            timeout=self.connect_timeout,
        )

    async def is_systemd_supported(
        self,
        host: str,
        port: int,
        username: str,
        password: Optional[str] = None,
        private_key: Optional[str] = None,
        passphrase: Optional[str] = None,
    ) -> bool:
        conn = None
        try:
            conn = await self._create_connection(
                host=host,
                port=port,
                username=username,
                password=password,
                private_key=private_key,
                passphrase=passphrase,
            )
            res = await asyncio.wait_for(
                conn.run("systemctl --version", check=False),
                timeout=self.command_timeout,
            )
            return res.exit_status == 0 and ("systemd" in res.stdout or "systemctl" in res.stdout)
        except Exception:
            return False
        finally:
            if conn:
                conn.close()

    async def list_services(
        self,
        host: str,
        port: int,
        username: str,
        password: Optional[str] = None,
        private_key: Optional[str] = None,
        passphrase: Optional[str] = None,
        state: Optional[str] = None,
        limit: int = 100,
    ) -> ServiceListResult:
        limit = max(1, min(limit, 200))
        conn = None
        try:
            conn = await self._create_connection(
                host=host,
                port=port,
                username=username,
                password=password,
                private_key=private_key,
                passphrase=passphrase,
            )

            # Check systemd support first
            check_res = await asyncio.wait_for(
                conn.run("systemctl --version", check=False),
                timeout=self.command_timeout,
            )
            if check_res.exit_status != 0 or ("systemd" not in check_res.stdout and "systemctl" not in check_res.stdout):
                return ServiceListResult(
                    systemd_supported=False,
                    services=[],
                    error_message="Systemd tidak didukung atau tidak aktif pada server ini.",
                )

            # Build list-units command
            cmd = "systemctl list-units --type=service --all --no-legend --no-pager"
            if state and state in ("active", "inactive", "failed"):
                cmd = f"systemctl list-units --type=service --state={state} --no-legend --no-pager"

            res = await asyncio.wait_for(
                conn.run(cmd, check=False),
                timeout=self.command_timeout,
            )

            services: List[ServiceInfo] = []
            for line in res.stdout.strip().splitlines():
                if not line.strip():
                    continue

                parts = line.strip().split()
                # If bullet point icon exists (e.g. ● or *), drop it
                if parts and parts[0] in ("●", "*"):
                    parts = parts[1:]

                if len(parts) < 4:
                    continue

                name = parts[0]
                if not name.endswith(".service"):
                    continue

                load_state = parts[1]
                active_state = parts[2]
                sub_state = parts[3]
                description = " ".join(parts[4:]) if len(parts) > 4 else None

                services.append(
                    ServiceInfo(
                        name=name,
                        load_state=load_state,
                        active_state=active_state,
                        sub_state=sub_state,
                        description=description,
                    )
                )

                if len(services) >= limit:
                    break

            return ServiceListResult(
                systemd_supported=True,
                services=services,
            )

        except (asyncssh.PermissionDenied, OSError, asyncio.TimeoutError, TimeoutError, asyncssh.Error, ValueError) as e:
            logger.warning("SSH connection error during list_services: %s", type(e).__name__)
            return ServiceListResult(
                systemd_supported=False,
                services=[],
                error_message=f"Gagal menghubungkan ke server SSH: {type(e).__name__}",
            )
        except Exception as e:
            logger.error("Unexpected error during list_services: %s", type(e).__name__)
            return ServiceListResult(
                systemd_supported=False,
                services=[],
                error_message="Terjadi kesalahan saat mengambil daftar service.",
            )
        finally:
            if conn:
                conn.close()

    async def get_service(
        self,
        host: str,
        port: int,
        username: str,
        password: Optional[str] = None,
        private_key: Optional[str] = None,
        passphrase: Optional[str] = None,
        service_name: str = "",
    ) -> Optional[ServiceInfo]:
        if not SERVICE_NAME_PATTERN.match(service_name):
            raise ValueError(f"Nama service tidak valid: {service_name}")

        conn = None
        try:
            conn = await self._create_connection(
                host=host,
                port=port,
                username=username,
                password=password,
                private_key=private_key,
                passphrase=passphrase,
            )

            cmd = (
                f"systemctl show {service_name} "
                "--property=Id,Description,LoadState,ActiveState,SubState,UnitFileState,MainPID,ActiveEnterTimestamp"
            )
            res = await asyncio.wait_for(
                conn.run(cmd, check=False),
                timeout=self.command_timeout,
            )

            props: Dict[str, str] = {}
            for line in res.stdout.strip().splitlines():
                if "=" in line:
                    k, v = line.split("=", 1)
                    props[k.strip()] = v.strip()

            id_val = props.get("Id", service_name)
            load_state = props.get("LoadState", "unknown")
            active_state = props.get("ActiveState", "unknown")
            sub_state = props.get("SubState", "unknown")
            description = props.get("Description") or None
            unit_file_state = props.get("UnitFileState", "").lower()

            enabled: Optional[bool] = None
            if unit_file_state in ("enabled", "enabled-runtime", "static", "alias", "indirect"):
                enabled = True
            elif unit_file_state in ("disabled", "masked", "masked-runtime"):
                enabled = False

            main_pid: Optional[int] = None
            raw_pid = props.get("MainPID")
            if raw_pid and raw_pid.isdigit():
                pid_int = int(raw_pid)
                if pid_int > 0:
                    main_pid = pid_int

            active_enter = props.get("ActiveEnterTimestamp")
            if active_enter and active_enter.lower() in ("", "n/a", "0"):
                active_enter = None

            return ServiceInfo(
                name=id_val if id_val else service_name,
                load_state=load_state,
                active_state=active_state,
                sub_state=sub_state,
                description=description,
                enabled=enabled,
                main_pid=main_pid,
                active_enter_timestamp=active_enter,
            )

        except Exception as e:
            logger.warning("Error fetching service detail for %s: %s", service_name, type(e).__name__)
            return None
        finally:
            if conn:
                conn.close()

    async def execute_action(
        self,
        host: str,
        port: int,
        username: str,
        password: Optional[str] = None,
        private_key: Optional[str] = None,
        passphrase: Optional[str] = None,
        service_name: str = "",
        action: str = "",
    ) -> ServiceActionResult:
        if action not in ALLOWED_ACTIONS:
            return ServiceActionResult(
                success=False,
                service=service_name,
                action=action,
                message=f"Aksi service '{action}' tidak diizinkan. Hanya start, stop, restart, reload yang diperbolehkan.",
                error="INVALID_ACTION",
            )

        if not SERVICE_NAME_PATTERN.match(service_name):
            return ServiceActionResult(
                success=False,
                service=service_name,
                action=action,
                message="Nama service tidak valid.",
                error="INVALID_SERVICE_NAME",
            )

        conn = None
        try:
            conn = await self._create_connection(
                host=host,
                port=port,
                username=username,
                password=password,
                private_key=private_key,
                passphrase=passphrase,
            )

            # Get previous state
            prev_info = await self._get_service_with_conn(conn, service_name)
            prev_state_dict = (
                {"active_state": prev_info.active_state, "sub_state": prev_info.sub_state}
                if prev_info
                else None
            )

            # Execute action using sudo -n or direct if root
            if username == "root":
                cmd = f"systemctl {action} {service_name}"
            else:
                cmd = f"sudo -n systemctl {action} {service_name}"

            res = await asyncio.wait_for(
                conn.run(cmd, check=False),
                timeout=self.command_timeout,
            )

            # Check for sudo password errors in stderr
            stderr_lower = (res.stderr or "").lower()
            if res.exit_status != 0:
                if any(
                    phrase in stderr_lower
                    for phrase in (
                        "password is required",
                        "a password is required",
                        "interactive authentication required",
                        "sudo: a terminal is required",
                        "sudo: no tty present",
                    )
                ):
                    curr_info = await self._get_service_with_conn(conn, service_name)
                    curr_state_dict = (
                        {"active_state": curr_info.active_state, "sub_state": curr_info.sub_state}
                        if curr_info
                        else None
                    )
                    return ServiceActionResult(
                        success=False,
                        service=service_name,
                        action=action,
                        previous_state=prev_state_dict,
                        current_state=curr_state_dict,
                        message="Operasi service membutuhkan akses passwordless sudo atau root.",
                        error="SUDO_PASSWORD_REQUIRED",
                    )

            # Query current state after action
            curr_info = await self._get_service_with_conn(conn, service_name)
            curr_state_dict = (
                {"active_state": curr_info.active_state, "sub_state": curr_info.sub_state}
                if curr_info
                else None
            )

            # Determine success based on exit status and states
            if res.exit_status == 0:
                return ServiceActionResult(
                    success=True,
                    service=service_name,
                    action=action,
                    previous_state=prev_state_dict,
                    current_state=curr_state_dict,
                    message=f"Service {service_name} berhasil di-{action}.",
                )
            else:
                return ServiceActionResult(
                    success=False,
                    service=service_name,
                    action=action,
                    previous_state=prev_state_dict,
                    current_state=curr_state_dict,
                    message=f"Gagal melakukan {action} pada {service_name}.",
                    error="OPERATION_FAILED",
                )

        except (asyncio.TimeoutError, TimeoutError):
            return ServiceActionResult(
                success=False,
                service=service_name,
                action=action,
                message=f"Operasi service batas waktu (timeout {self.command_timeout}s).",
                error="TIMEOUT",
            )
        except Exception as e:
            logger.error("Service action execution error: %s", type(e).__name__)
            return ServiceActionResult(
                success=False,
                service=service_name,
                action=action,
                message=f"Terjadi kesalahan saat menjalankan aksi {action}.",
                error="INTERNAL_ERROR",
            )
        finally:
            if conn:
                conn.close()

    async def _get_service_with_conn(self, conn, service_name: str) -> Optional[ServiceInfo]:
        try:
            cmd = (
                f"systemctl show {service_name} "
                "--property=Id,Description,LoadState,ActiveState,SubState,UnitFileState,MainPID,ActiveEnterTimestamp"
            )
            res = await asyncio.wait_for(
                conn.run(cmd, check=False),
                timeout=self.command_timeout,
            )
            props: Dict[str, str] = {}
            for line in res.stdout.strip().splitlines():
                if "=" in line:
                    k, v = line.split("=", 1)
                    props[k.strip()] = v.strip()

            id_val = props.get("Id", service_name)
            load_state = props.get("LoadState", "unknown")
            active_state = props.get("ActiveState", "unknown")
            sub_state = props.get("SubState", "unknown")
            description = props.get("Description") or None
            unit_file_state = props.get("UnitFileState", "").lower()

            enabled: Optional[bool] = None
            if unit_file_state in ("enabled", "enabled-runtime", "static", "alias", "indirect"):
                enabled = True
            elif unit_file_state in ("disabled", "masked", "masked-runtime"):
                enabled = False

            main_pid: Optional[int] = None
            raw_pid = props.get("MainPID")
            if raw_pid and raw_pid.isdigit():
                pid_int = int(raw_pid)
                if pid_int > 0:
                    main_pid = pid_int

            active_enter = props.get("ActiveEnterTimestamp")
            if active_enter and active_enter.lower() in ("", "n/a", "0"):
                active_enter = None

            return ServiceInfo(
                name=id_val if id_val else service_name,
                load_state=load_state,
                active_state=active_state,
                sub_state=sub_state,
                description=description,
                enabled=enabled,
                main_pid=main_pid,
                active_enter_timestamp=active_enter,
            )
        except Exception:
            return None
