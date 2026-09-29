import asyncio
from datetime import datetime, timezone
import json
import logging
import re
from typing import Dict, List, Optional
import asyncssh

from app.core.config import settings
from app.infrastructure.docker_providers.base import (
    DockerProvider,
    DockerStatusResult,
    ContainerSummaryResult,
    ContainerDetailResult,
    ContainerActionResult,
    ContainerLogEntryResult,
    ContainerLogsResult,
    ComposeStatusResult,
    ComposeServiceStatusResult,
    ComposeActionResult,
)
from app.schemas.docker import (
    CONTAINER_ID_PATTERN,
    PROJECT_NAME_PATTERN,
    COMPOSE_FILE_PATTERN,
)
from app.services.redaction import secret_redactor

logger = logging.getLogger(__name__)

SINCE_MAP = {
    "5m": "5m",
    "10m": "10m",
    "30m": "30m",
    "1h": "1h",
    "6h": "6h",
    "12h": "12h",
    "24h": "24h",
}


class SSHDockerProvider(DockerProvider):
    """Docker and Docker Compose provider over SSH."""

    def __init__(
        self,
        connect_timeout: int = settings.DOCKER_CONNECTION_TIMEOUT,
        command_timeout: int = settings.DOCKER_COMMAND_TIMEOUT,
        log_command_timeout: int = settings.DOCKER_LOG_COMMAND_TIMEOUT,
        compose_command_timeout: int = settings.DOCKER_COMPOSE_COMMAND_TIMEOUT,
        max_log_bytes: int = settings.MAX_DOCKER_LOG_RESPONSE_BYTES,
    ):
        self.connect_timeout = connect_timeout
        self.command_timeout = command_timeout
        self.log_command_timeout = log_command_timeout
        self.compose_command_timeout = compose_command_timeout
        self.max_log_bytes = max_log_bytes

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
                logger.warning("Invalid SSH private key for Docker: %s", type(e).__name__)
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

    async def _run_docker_cmd(self, conn, cmd: str, timeout: int) -> tuple[int, str, str]:
        """Run docker command with automatic sudo -n fallback."""
        try:
            res = await asyncio.wait_for(conn.run(cmd, check=False), timeout=timeout)
            if res.exit_status == 0:
                return (res.exit_status, res.stdout or "", res.stderr or "")

            # If failed or permission denied, attempt sudo -n
            err_lower = (res.stderr or "").lower()
            if res.exit_status != 0 or "permission denied" in err_lower or "got permission denied" in err_lower:
                sudo_cmd = f"sudo -n {cmd}"
                sudo_res = await asyncio.wait_for(conn.run(sudo_cmd, check=False), timeout=timeout)
                return (sudo_res.exit_status, sudo_res.stdout or "", sudo_res.stderr or "")

            return (res.exit_status, res.stdout or "", res.stderr or "")
        except Exception as e:
            logger.debug("Error running docker command '%s': %s", cmd, e)
            raise

    async def get_docker_status(
        self,
        host: str,
        port: int,
        username: str,
        password: Optional[str] = None,
        private_key: Optional[str] = None,
        passphrase: Optional[str] = None,
    ) -> DockerStatusResult:
        conn = None
        try:
            conn = await self._create_connection(host, port, username, password, private_key, passphrase)

            # Check if docker binary exists
            which_res = await asyncio.wait_for(
                conn.run("which docker 2>/dev/null", check=False),
                timeout=self.command_timeout,
            )
            if which_res.exit_status != 0:
                return DockerStatusResult(installed=False, running=False, state="NOT_INSTALLED")

            # Check docker version
            status_code, stdout, stderr = await self._run_docker_cmd(
                conn, "docker version --format '{{.Server.Version}}'", self.command_timeout
            )

            version = stdout.strip().strip("'\"") if status_code == 0 and stdout.strip() else None

            # Verify docker daemon running via docker info
            info_code, info_out, info_err = await self._run_docker_cmd(
                conn, "docker info --format '{{.ServerVersion}}'", self.command_timeout
            )

            if info_code == 0:
                detected_version = info_out.strip() or version or "Available"
                return DockerStatusResult(
                    installed=True,
                    running=True,
                    version=detected_version,
                    state="RUNNING",
                )
            else:
                err_str = (info_err + " " + stderr).lower()
                if "is the docker daemon running" in err_str or "cannot connect to the docker daemon" in err_str:
                    return DockerStatusResult(
                        installed=True,
                        running=False,
                        version=version,
                        state="STOPPED",
                    )
                elif "permission denied" in err_str:
                    return DockerStatusResult(
                        installed=True,
                        running=False,
                        version=version,
                        state="STOPPED",
                        error="PERMISSION_DENIED",
                    )
                return DockerStatusResult(
                    installed=True,
                    running=False,
                    version=version,
                    state="UNKNOWN",
                )

        except (asyncio.TimeoutError, TimeoutError):
            return DockerStatusResult(installed=False, running=False, state="UNKNOWN", error="TIMEOUT")
        except Exception as e:
            logger.warning("Error detecting docker: %s", e)
            return DockerStatusResult(installed=False, running=False, state="UNKNOWN", error="SSH_UNAVAILABLE")
        finally:
            if conn:
                conn.close()

    async def list_containers(
        self,
        host: str,
        port: int,
        username: str,
        password: Optional[str] = None,
        private_key: Optional[str] = None,
        passphrase: Optional[str] = None,
        state_filter: str = "running",
    ) -> List[ContainerSummaryResult]:
        conn = None
        try:
            conn = await self._create_connection(host, port, username, password, private_key, passphrase)

            flag = "-a" if state_filter in ["all", "stopped"] else ""
            cmd = f"docker ps {flag} --format '{{{{json .}}}}' --no-trunc"

            code, stdout, stderr = await self._run_docker_cmd(conn, cmd, self.command_timeout)
            if code != 0:
                logger.warning("Failed to list docker containers: %s", stderr)
                return []

            containers: List[ContainerSummaryResult] = []
            for line in stdout.strip().splitlines():
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                    c_id = str(data.get("ID", ""))[:12]
                    name = str(data.get("Names", "")).strip().split(",")[0].lstrip("/")
                    image = str(data.get("Image", ""))
                    status = str(data.get("Status", ""))
                    state = str(data.get("State", "")).lower() or ("running" if "Up" in status else "exited")
                    created = data.get("CreatedAt")

                    raw_ports = str(data.get("Ports", "")).strip()
                    ports = [p.strip() for p in raw_ports.split(",") if p.strip()] if raw_ports else []

                    # Filter if stopped requested
                    if state_filter == "stopped" and state == "running":
                        continue

                    containers.append(
                        ContainerSummaryResult(
                            id=c_id,
                            name=name,
                            image=image,
                            status=status,
                            state=state,
                            created_at=created,
                            ports=ports,
                        )
                    )
                except Exception as ex:
                    logger.debug("Error parsing container JSON line: %s", ex)
                    continue

            return containers
        except Exception as e:
            logger.warning("Error listing containers: %s", e)
            return []
        finally:
            if conn:
                conn.close()

    async def get_container_detail(
        self,
        host: str,
        port: int,
        username: str,
        password: Optional[str] = None,
        private_key: Optional[str] = None,
        passphrase: Optional[str] = None,
        container_id: str = "",
    ) -> Optional[ContainerDetailResult]:
        if not CONTAINER_ID_PATTERN.match(container_id):
            return None

        conn = None
        try:
            conn = await self._create_connection(host, port, username, password, private_key, passphrase)

            cmd = f"docker inspect {container_id}"
            code, stdout, stderr = await self._run_docker_cmd(conn, cmd, self.command_timeout)
            if code != 0 or not stdout.strip():
                return None

            data_list = json.loads(stdout)
            if not data_list or not isinstance(data_list, list):
                return None

            data = data_list[0]
            c_id = str(data.get("Id", container_id))[:12]
            name = str(data.get("Name", "")).lstrip("/")
            config = data.get("Config", {})
            image = config.get("Image", "")
            state_obj = data.get("State", {})
            state = str(state_obj.get("Status", "")).lower() or ("running" if state_obj.get("Running") else "exited")
            created_at = data.get("Created")
            started_at = state_obj.get("StartedAt")

            host_config = data.get("HostConfig", {})
            restart_policy = host_config.get("RestartPolicy", {}).get("Name", "no")

            # Extract ports
            ports: List[str] = []
            network_settings = data.get("NetworkSettings", {})
            port_bindings = network_settings.get("Ports", {}) or {}
            for container_port, bindings in port_bindings.items():
                if bindings:
                    for b in bindings:
                        host_port = b.get("HostPort")
                        if host_port:
                            ports.append(f"{host_port}:{container_port}")
                else:
                    ports.append(container_port)

            # Basic stats / resource info (quick one-shot)
            cpu_usage = None
            memory_usage = None
            try:
                stats_cmd = f"docker stats --no-stream --format '{{{{.CPUPerc}}}}|{{{{.MemUsage}}}}' {container_id}"
                s_code, s_out, _ = await self._run_docker_cmd(conn, stats_cmd, 5)
                if s_code == 0 and s_out.strip() and "|" in s_out:
                    parts = s_out.strip().split("|")
                    cpu_usage = parts[0].strip()
                    memory_usage = parts[1].strip()
            except Exception:
                pass

            status_str = f"Up since {started_at[:19]}" if state == "running" else f"Exited ({state_obj.get('ExitCode', 0)})"

            return ContainerDetailResult(
                id=c_id,
                name=name,
                image=image,
                state=state,
                status=status_str,
                created_at=created_at,
                started_at=started_at,
                ports=ports,
                restart_policy=restart_policy,
                cpu_usage=cpu_usage,
                memory_usage=memory_usage,
            )

        except Exception as e:
            logger.warning("Error getting container detail: %s", e)
            return None
        finally:
            if conn:
                conn.close()

    async def execute_container_action(
        self,
        host: str,
        port: int,
        username: str,
        password: Optional[str] = None,
        private_key: Optional[str] = None,
        passphrase: Optional[str] = None,
        container_id: str = "",
        action: str = "restart",
    ) -> ContainerActionResult:
        if not CONTAINER_ID_PATTERN.match(container_id):
            return ContainerActionResult(
                success=False,
                container=container_id,
                action=action,
                current_state="unknown",
                message="Container ID atau nama container tidak valid.",
                error="INVALID_CONTAINER_ID",
            )

        if action not in ["start", "stop", "restart"]:
            return ContainerActionResult(
                success=False,
                container=container_id,
                action=action,
                current_state="unknown",
                message="Aksi container tidak didukung.",
                error="INVALID_ACTION",
            )

        conn = None
        try:
            conn = await self._create_connection(host, port, username, password, private_key, passphrase)

            cmd = f"docker {action} {container_id}"
            code, stdout, stderr = await self._run_docker_cmd(conn, cmd, self.command_timeout)

            # Query current status after action
            inspect_cmd = f"docker inspect --format '{{{{.State.Status}}}}' {container_id}"
            _, ins_out, _ = await self._run_docker_cmd(conn, inspect_cmd, self.command_timeout)
            current_state = ins_out.strip().lower() or ("running" if action in ["start", "restart"] and code == 0 else "unknown")

            if code == 0:
                return ContainerActionResult(
                    success=True,
                    container=container_id,
                    action=action,
                    current_state=current_state,
                    message=f"Container {container_id} berhasil di-{action}.",
                )
            else:
                err_msg = "Gagal menjalankan aksi container."
                if "No such container" in stderr:
                    err_msg = f"Container {container_id} tidak ditemukan."
                elif "permission denied" in stderr.lower():
                    err_msg = "Permission denied saat mengakses Docker daemon."
                return ContainerActionResult(
                    success=False,
                    container=container_id,
                    action=action,
                    current_state=current_state,
                    message=err_msg,
                    error="ACTION_FAILED",
                )

        except (asyncio.TimeoutError, TimeoutError):
            return ContainerActionResult(
                success=False,
                container=container_id,
                action=action,
                current_state="unknown",
                message="Operasi container timed out.",
                error="TIMEOUT",
            )
        except Exception as e:
            logger.warning("Error executing container action: %s", e)
            return ContainerActionResult(
                success=False,
                container=container_id,
                action=action,
                current_state="unknown",
                message="Gagal terhubung ke server target.",
                error="SSH_UNAVAILABLE",
            )
        finally:
            if conn:
                conn.close()

    async def get_container_logs(
        self,
        host: str,
        port: int,
        username: str,
        password: Optional[str] = None,
        private_key: Optional[str] = None,
        passphrase: Optional[str] = None,
        container_id: str = "",
        lines: int = 100,
        since: Optional[str] = None,
    ) -> ContainerLogsResult:
        if not CONTAINER_ID_PATTERN.match(container_id):
            return ContainerLogsResult(
                container=container_id,
                lines_requested=lines,
                lines_returned=0,
                error="INVALID_CONTAINER_ID",
            )

        clamped_lines = max(10, min(lines, 1000))
        since_arg = f"--since {SINCE_MAP[since]}" if since and since in SINCE_MAP else ""

        conn = None
        try:
            conn = await self._create_connection(host, port, username, password, private_key, passphrase)

            cmd = f"docker logs --tail {clamped_lines} --timestamps {since_arg} {container_id}"
            code, stdout, stderr = await self._run_docker_cmd(conn, cmd, self.log_command_timeout)

            # Docker logs outputs stdout and stderr together
            output_text = stdout if stdout else stderr
            raw_lines = [l for l in output_text.splitlines() if l.strip()]

            entries: List[ContainerLogEntryResult] = []
            total_bytes = 0
            is_truncated = False

            # Pattern for Docker ISO timestamp prefix: 2026-09-29T05:30:00.123456789Z
            iso_pattern = re.compile(r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z?)\s+(.*)$")

            for line in raw_lines:
                timestamp = None
                msg = line
                match = iso_pattern.match(line)
                if match:
                    ts_str = match.group(1).rstrip("Z")
                    msg = match.group(2)
                    try:
                        timestamp = datetime.fromisoformat(ts_str).replace(tzinfo=timezone.utc)
                    except Exception:
                        pass

                redacted_msg = secret_redactor.redact(msg)
                entry_bytes = len(redacted_msg.encode("utf-8"))
                if total_bytes + entry_bytes > self.max_log_bytes:
                    is_truncated = True
                    break

                total_bytes += entry_bytes
                entries.append(ContainerLogEntryResult(timestamp=timestamp, message=redacted_msg))

            return ContainerLogsResult(
                container=container_id,
                lines_requested=clamped_lines,
                lines_returned=len(entries),
                truncated=is_truncated,
                entries=entries,
            )

        except (asyncio.TimeoutError, TimeoutError):
            return ContainerLogsResult(
                container=container_id,
                lines_requested=clamped_lines,
                lines_returned=0,
                error="TIMEOUT",
            )
        except Exception as e:
            logger.warning("Error getting container logs: %s", e)
            return ContainerLogsResult(
                container=container_id,
                lines_requested=clamped_lines,
                lines_returned=0,
                error="SSH_UNAVAILABLE",
            )
        finally:
            if conn:
                conn.close()

    async def get_compose_status(
        self,
        host: str,
        port: int,
        username: str,
        password: Optional[str] = None,
        private_key: Optional[str] = None,
        passphrase: Optional[str] = None,
        working_directory: str = "",
        compose_file: str = "docker-compose.yml",
        project_name: str = "",
    ) -> ComposeStatusResult:
        if not PROJECT_NAME_PATTERN.match(project_name) or not COMPOSE_FILE_PATTERN.match(compose_file):
            return ComposeStatusResult(
                project_name=project_name,
                status="UNKNOWN",
                error="INVALID_PROJECT_CONFIG",
            )

        conn = None
        try:
            conn = await self._create_connection(host, port, username, password, private_key, passphrase)

            # Check if docker compose or docker-compose is available
            cmd = f"cd '{working_directory}' && docker compose -f '{compose_file}' -p '{project_name}' ps --format json"
            code, stdout, stderr = await self._run_docker_cmd(conn, cmd, self.command_timeout)

            if code != 0:
                # Try classic docker-compose command
                cmd_v1 = f"cd '{working_directory}' && docker-compose -f '{compose_file}' -p '{project_name}' ps"
                code_v1, stdout_v1, _ = await self._run_docker_cmd(conn, cmd_v1, self.command_timeout)
                if code_v1 != 0:
                    return ComposeStatusResult(
                        project_name=project_name,
                        status="UNKNOWN",
                        error="COMPOSE_UNAVAILABLE",
                    )

            services: List[ComposeServiceStatusResult] = []
            running_count = 0
            total_count = 0

            # Parse JSON output from docker compose ps
            for line in stdout.strip().splitlines():
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                    name = str(data.get("Name", ""))
                    service = str(data.get("Service", name))
                    state = str(data.get("State", "")).lower() or ("running" if "Up" in str(data.get("Status", "")) else "stopped")
                    status_str = str(data.get("Status", ""))

                    total_count += 1
                    if state == "running":
                        running_count += 1

                    services.append(
                        ComposeServiceStatusResult(
                            name=name,
                            service=service,
                            state=state,
                            status=status_str,
                        )
                    )
                except Exception:
                    continue

            if total_count == 0:
                project_status = "STOPPED"
            elif running_count == total_count:
                project_status = "RUNNING"
            elif running_count > 0:
                project_status = "PARTIAL"
            else:
                project_status = "STOPPED"

            return ComposeStatusResult(
                project_name=project_name,
                status=project_status,
                services=services,
            )

        except Exception as e:
            logger.warning("Error getting compose status: %s", e)
            return ComposeStatusResult(
                project_name=project_name,
                status="UNKNOWN",
                error="SSH_UNAVAILABLE",
            )
        finally:
            if conn:
                conn.close()

    async def execute_compose_action(
        self,
        host: str,
        port: int,
        username: str,
        password: Optional[str] = None,
        private_key: Optional[str] = None,
        passphrase: Optional[str] = None,
        working_directory: str = "",
        compose_file: str = "docker-compose.yml",
        project_name: str = "",
        action: str = "restart",
    ) -> ComposeActionResult:
        if not PROJECT_NAME_PATTERN.match(project_name) or not COMPOSE_FILE_PATTERN.match(compose_file):
            return ComposeActionResult(
                success=False,
                project_name=project_name,
                action=action,
                status="UNKNOWN",
                message="Konfigurasi Docker Compose project tidak valid.",
                error="INVALID_PROJECT_CONFIG",
            )

        if action not in ["up", "down", "restart"]:
            return ComposeActionResult(
                success=False,
                project_name=project_name,
                action=action,
                status="UNKNOWN",
                message="Aksi Compose tidak didukung.",
                error="INVALID_ACTION",
            )

        action_cmd_map = {
            "up": "up -d",
            "down": "down",
            "restart": "restart",
        }

        conn = None
        try:
            conn = await self._create_connection(host, port, username, password, private_key, passphrase)

            sub_cmd = action_cmd_map[action]
            cmd = f"cd '{working_directory}' && docker compose -f '{compose_file}' -p '{project_name}' {sub_cmd}"
            code, stdout, stderr = await self._run_docker_cmd(conn, cmd, self.compose_command_timeout)

            # Query status after action
            status_res = await self.get_compose_status(
                host, port, username, password, private_key, passphrase,
                working_directory, compose_file, project_name
            )

            if code == 0:
                return ComposeActionResult(
                    success=True,
                    project_name=project_name,
                    action=action,
                    status=status_res.status,
                    message=f"Docker Compose '{project_name}' berhasil di-{action}.",
                )
            else:
                return ComposeActionResult(
                    success=False,
                    project_name=project_name,
                    action=action,
                    status=status_res.status,
                    message=f"Gagal menjalankan '{action}' pada Docker Compose '{project_name}'.",
                    error="COMPOSE_ACTION_FAILED",
                )

        except (asyncio.TimeoutError, TimeoutError):
            return ComposeActionResult(
                success=False,
                project_name=project_name,
                action=action,
                status="UNKNOWN",
                message=f"Operasi Compose '{action}' timed out.",
                error="TIMEOUT",
            )
        except Exception as e:
            logger.warning("Error executing compose action: %s", e)
            return ComposeActionResult(
                success=False,
                project_name=project_name,
                action=action,
                status="UNKNOWN",
                message="Gagal terhubung ke server target via SSH.",
                error="SSH_UNAVAILABLE",
            )
        finally:
            if conn:
                conn.close()
