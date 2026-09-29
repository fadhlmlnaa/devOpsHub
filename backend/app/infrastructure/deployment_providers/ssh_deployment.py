import asyncio
from datetime import datetime, timezone
import logging
import shlex
from typing import Any, Callable, Dict, List, Optional
import asyncssh

from app.core.config import settings
from app.infrastructure.deployment_providers.base import (
    DeploymentProvider,
    DeploymentExecutionResult,
)
from app.services.redaction import secret_redactor

logger = logging.getLogger(__name__)


class SSHDeploymentProvider(DeploymentProvider):
    """Deployment provider implementing predefined workflows via SSH."""

    def __init__(
        self,
        connect_timeout: int = settings.DEPLOYMENT_CONNECTION_TIMEOUT,
        command_timeout: int = settings.DEPLOYMENT_COMMAND_TIMEOUT,
        max_duration: int = settings.DEPLOYMENT_MAX_DURATION,
        max_log_lines: int = settings.MAX_DEPLOYMENT_LOG_LINES,
        max_log_msg_len: int = settings.MAX_DEPLOYMENT_LOG_MESSAGE_LENGTH,
    ):
        self.connect_timeout = connect_timeout
        self.command_timeout = command_timeout
        self.max_duration = max_duration
        self.max_log_lines = max_log_lines
        self.max_log_msg_len = max_log_msg_len

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
                logger.warning("Invalid SSH private key for deployment: %s", type(e).__name__)
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

    async def validate_environment(
        self,
        host: str,
        port: int,
        username: str,
        password: Optional[str] = None,
        private_key: Optional[str] = None,
        passphrase: Optional[str] = None,
        config: Any = None,
    ) -> tuple[bool, str]:
        conn = None
        try:
            conn = await self._create_connection(host, port, username, password, private_key, passphrase)
            working_dir = shlex.quote(config.working_directory)
            res = await asyncio.wait_for(
                conn.run(f"test -d {working_dir}", check=False),
                timeout=self.command_timeout,
            )
            if res.exit_status != 0:
                return False, f"Working directory '{config.working_directory}' does not exist on target server."
            return True, "Environment validated successfully."
        except Exception as e:
            return False, f"Failed to connect to server: {str(e)}"
        finally:
            if conn:
                conn.close()

    async def deploy(
        self,
        host: str,
        port: int,
        username: str,
        password: Optional[str] = None,
        private_key: Optional[str] = None,
        passphrase: Optional[str] = None,
        config: Any = None,
        log_callback: Optional[Callable[[str, str], Any]] = None,
    ) -> DeploymentExecutionResult:
        logs: List[Dict[str, Any]] = []
        seq = 1

        def add_log(level: str, raw_msg: str):
            nonlocal seq
            if len(logs) >= self.max_log_lines:
                return
            cleaned_msg = secret_redactor.redact(raw_msg)
            if len(cleaned_msg) > self.max_log_msg_len:
                cleaned_msg = cleaned_msg[: self.max_log_msg_len] + " [TRUNCATED]"
            entry = {
                "sequence": seq,
                "timestamp": datetime.now(timezone.utc),
                "level": level,
                "message": cleaned_msg,
            }
            logs.append(entry)
            seq += 1
            if log_callback:
                try:
                    log_callback(level, cleaned_msg, entry["sequence"], entry["timestamp"])
                except Exception:
                    pass

        conn = None
        commit_ref = None
        try:
            add_log("INFO", f"Memulai deployment '{config.name}' pada server {host}:{port}")
            add_log("INFO", f"Menghubungkan ke SSH server sebagai user '{username}'...")

            conn = await self._create_connection(host, port, username, password, private_key, passphrase)
            add_log("INFO", "Koneksi SSH berhasil tersambung.")

            working_dir = shlex.quote(config.working_directory)

            # 1. Validasi working directory
            check_dir = await asyncio.wait_for(
                conn.run(f"test -d {working_dir}", check=False),
                timeout=self.command_timeout,
            )
            if check_dir.exit_status != 0:
                err_msg = f"Direktori kerja '{config.working_directory}' tidak ditemukan pada server."
                add_log("ERROR", err_msg)
                return DeploymentExecutionResult(
                    success=False,
                    status="FAILED",
                    message="Direktori kerja tidak ditemukan.",
                    error_message=err_msg,
                    logs=logs,
                )

            add_log("INFO", f"Direktori kerja tervalidasi: {config.working_directory}")

            # Define sequence of steps to execute
            # If explicit steps configured in JSON, use those. Otherwise build standard workflow based on deployment_type
            all_steps = []
            if config.pre_deploy_steps:
                all_steps.extend(config.pre_deploy_steps)
            if config.deploy_steps:
                all_steps.extend(config.deploy_steps)
            if config.post_deploy_steps:
                all_steps.extend(config.post_deploy_steps)

            # If no explicit steps configured, use standard default workflow
            if not all_steps:
                if config.deployment_type == "DOCKER_COMPOSE":
                    all_steps = [
                        {"operation": "GIT_PULL"} if config.branch or config.repository_url else None,
                        {"operation": "DOCKER_COMPOSE_PULL"},
                        {"operation": "DOCKER_COMPOSE_UP"},
                        {"operation": "HEALTH_CHECK"},
                    ]
                else:  # SYSTEMD
                    all_steps = [
                        {"operation": "GIT_PULL"} if config.branch or config.repository_url else None,
                        {"operation": "INSTALL_DEPENDENCIES"},
                        {"operation": "BUILD"},
                        {"operation": "RESTART_SERVICE"} if config.restart_service_name else None,
                        {"operation": "HEALTH_CHECK"},
                    ]
                all_steps = [s for s in all_steps if s is not None]

            # Execute operations
            for step_item in all_steps:
                op = step_item.get("operation") if isinstance(step_item, dict) else getattr(step_item, "operation", None)
                if hasattr(op, "value"):
                    op = op.value
                op = str(op).upper() if op else ""

                if op == "GIT_PULL":
                    add_log("INFO", f"Menjalankan operasi GIT_PULL pada {config.working_directory}...")
                    branch_cmd = ""
                    if config.branch:
                        safe_branch = shlex.quote(config.branch)
                        branch_cmd = f"git checkout {safe_branch} && git pull origin {safe_branch}"
                    else:
                        branch_cmd = "git pull"

                    git_res = await asyncio.wait_for(
                        conn.run(f"cd {working_dir} && {branch_cmd}", check=False),
                        timeout=self.command_timeout,
                    )
                    if git_res.stdout:
                        add_log("INFO", git_res.stdout.strip())
                    if git_res.exit_status != 0:
                        add_log("ERROR", f"Git pull gagal: {git_res.stderr.strip() if git_res.stderr else 'Unknown error'}")
                        return DeploymentExecutionResult(
                            success=False,
                            status="FAILED",
                            message="Git pull gagal.",
                            error_message=git_res.stderr.strip() if git_res.stderr else "Git pull failed",
                            logs=logs,
                        )

                    # Get latest commit ref
                    rev_res = await asyncio.wait_for(
                        conn.run(f"cd {working_dir} && git rev-parse --short HEAD", check=False),
                        timeout=self.command_timeout,
                    )
                    if rev_res.exit_status == 0 and rev_res.stdout.strip():
                        commit_ref = rev_res.stdout.strip()
                        add_log("INFO", f"Commit HEAD saat ini: {commit_ref}")

                elif op == "INSTALL_DEPENDENCIES":
                    add_log("INFO", "Memeriksa dan menginstal dependensi aplikasi...")
                    # Controlled dependency check: package.json, requirements.txt, composer.json
                    check_pkg = await conn.run(f"cd {working_dir} && test -f package.json", check=False)
                    check_req = await conn.run(f"cd {working_dir} && test -f requirements.txt", check=False)
                    check_cmp = await conn.run(f"cd {working_dir} && test -f composer.json", check=False)

                    if check_pkg.exit_status == 0:
                        add_log("INFO", "Mendeteksi package.json. Menjalankan npm install --production...")
                        npm_res = await asyncio.wait_for(
                            conn.run(f"cd {working_dir} && npm install --production", check=False),
                            timeout=self.command_timeout * 2,
                        )
                        if npm_res.stdout:
                            add_log("INFO", npm_res.stdout.strip())
                        if npm_res.exit_status != 0:
                            add_log("WARNING", f"npm install mengembalikan exit code non-nol: {npm_res.stderr.strip()}")

                    elif check_req.exit_status == 0:
                        add_log("INFO", "Mendeteksi requirements.txt. Menginstal python dependencies...")
                        pip_res = await asyncio.wait_for(
                            conn.run(f"cd {working_dir} && pip install -r requirements.txt", check=False),
                            timeout=self.command_timeout * 2,
                        )
                        if pip_res.stdout:
                            add_log("INFO", pip_res.stdout.strip())
                        if pip_res.exit_status != 0:
                            add_log("WARNING", f"pip install warning: {pip_res.stderr.strip()}")

                    elif check_cmp.exit_status == 0:
                        add_log("INFO", "Mendeteksi composer.json. Menjalankan composer install...")
                        cmp_res = await asyncio.wait_for(
                            conn.run(f"cd {working_dir} && composer install --no-dev --no-interaction --prefer-dist", check=False),
                            timeout=self.command_timeout * 2,
                        )
                        if cmp_res.stdout:
                            add_log("INFO", cmp_res.stdout.strip())

                    else:
                        add_log("INFO", "Tidak ada file manifest dependensi standar yang memerlukan instalasi otomatis.")

                elif op == "BUILD":
                    add_log("INFO", "Memeriksa build script...")
                    check_build = await conn.run(f"cd {working_dir} && grep -q '\"build\":' package.json 2>/dev/null", check=False)
                    if check_build.exit_status == 0:
                        add_log("INFO", "Menjalankan npm run build...")
                        build_res = await asyncio.wait_for(
                            conn.run(f"cd {working_dir} && npm run build", check=False),
                            timeout=self.command_timeout * 3,
                        )
                        if build_res.stdout:
                            add_log("INFO", build_res.stdout.strip())
                        if build_res.exit_status != 0:
                            add_log("ERROR", f"Build gagal: {build_res.stderr.strip()}")
                            return DeploymentExecutionResult(
                                success=False,
                                status="FAILED",
                                message="Build aplikasi gagal.",
                                error_message=build_res.stderr.strip(),
                                logs=logs,
                            )
                    else:
                        add_log("INFO", "Tahap build dilewati (tidak ada build script yang perlu dijalankan).")

                elif op == "DOCKER_COMPOSE_PULL":
                    add_log("INFO", "Menjalankan docker compose pull...")
                    compose_res = await asyncio.wait_for(
                        conn.run(f"cd {working_dir} && docker compose pull", check=False),
                        timeout=self.command_timeout * 2,
                    )
                    if compose_res.exit_status != 0:
                        # try sudo fallback
                        compose_res = await asyncio.wait_for(
                            conn.run(f"cd {working_dir} && sudo -n docker compose pull", check=False),
                            timeout=self.command_timeout * 2,
                        )
                    if compose_res.stdout:
                        add_log("INFO", compose_res.stdout.strip())
                    if compose_res.exit_status != 0:
                        add_log("WARNING", f"docker compose pull notice: {compose_res.stderr.strip()}")

                elif op == "DOCKER_COMPOSE_UP":
                    add_log("INFO", "Menjalankan docker compose up -d...")
                    compose_up = await asyncio.wait_for(
                        conn.run(f"cd {working_dir} && docker compose up -d", check=False),
                        timeout=self.command_timeout * 2,
                    )
                    if compose_up.exit_status != 0:
                        compose_up = await asyncio.wait_for(
                            conn.run(f"cd {working_dir} && sudo -n docker compose up -d", check=False),
                            timeout=self.command_timeout * 2,
                        )
                    if compose_up.stdout:
                        add_log("INFO", compose_up.stdout.strip())
                    if compose_up.exit_status != 0:
                        add_log("ERROR", f"docker compose up gagal: {compose_up.stderr.strip()}")
                        return DeploymentExecutionResult(
                            success=False,
                            status="FAILED",
                            message="Docker compose up gagal.",
                            error_message=compose_up.stderr.strip(),
                            logs=logs,
                        )

                elif op == "RESTART_SERVICE":
                    srv = config.restart_service_name
                    if srv:
                        add_log("INFO", f"Merestart systemd service '{srv}'...")
                        safe_srv = shlex.quote(srv)
                        rst_res = await asyncio.wait_for(
                            conn.run(f"sudo -n systemctl restart {safe_srv}", check=False),
                            timeout=self.command_timeout,
                        )
                        if rst_res.exit_status != 0:
                            rst_res = await asyncio.wait_for(
                                conn.run(f"systemctl restart {safe_srv}", check=False),
                                timeout=self.command_timeout,
                            )
                        if rst_res.exit_status != 0:
                            add_log("ERROR", f"Gagal merestart service {srv}: {rst_res.stderr.strip()}")
                            return DeploymentExecutionResult(
                                success=False,
                                status="FAILED",
                                message=f"Gagal merestart service {srv}.",
                                error_message=rst_res.stderr.strip(),
                                logs=logs,
                            )
                        add_log("INFO", f"Service '{srv}' berhasil direstart.")

                elif op == "HEALTH_CHECK":
                    add_log("INFO", "Melakukan verifikasi health check...")
                    hc_type = getattr(config, "health_check_type", "NONE")
                    if hasattr(hc_type, "value"):
                        hc_type = hc_type.value

                    if hc_type == "SERVICE_STATUS" and config.restart_service_name:
                        safe_srv = shlex.quote(config.restart_service_name)
                        stat_res = await asyncio.wait_for(
                            conn.run(f"systemctl is-active {safe_srv}", check=False),
                            timeout=self.command_timeout,
                        )
                        is_act = stat_res.stdout.strip() == "active"
                        if is_act:
                            add_log("INFO", f"Health check passed: Service '{config.restart_service_name}' is active.")
                        else:
                            add_log("ERROR", f"Health check failed: Service '{config.restart_service_name}' status is {stat_res.stdout.strip()}.")
                            return DeploymentExecutionResult(
                                success=False,
                                status="FAILED",
                                message="Health check service gagal.",
                                error_message=f"Service status: {stat_res.stdout.strip()}",
                                logs=logs,
                            )

                    elif hc_type == "DOCKER_COMPOSE_STATUS":
                        ps_res = await asyncio.wait_for(
                            conn.run(f"cd {working_dir} && docker compose ps --format json", check=False),
                            timeout=self.command_timeout,
                        )
                        if ps_res.exit_status != 0:
                            ps_res = await asyncio.wait_for(
                                conn.run(f"cd {working_dir} && sudo -n docker compose ps --format json", check=False),
                                timeout=self.command_timeout,
                            )
                        add_log("INFO", "Docker compose health check: stack status retrieved.")

                    elif hc_type == "HTTP_HEALTH_CHECK" and config.health_check_url:
                        safe_url = shlex.quote(config.health_check_url)
                        add_log("INFO", f"Menguji HTTP endpoint {config.health_check_url}...")
                        curl_res = await asyncio.wait_for(
                            conn.run(f"curl -s -f -o /dev/null -w '%{{http_code}}' --max-time 10 {safe_url}", check=False),
                            timeout=self.command_timeout,
                        )
                        code_str = curl_res.stdout.strip()
                        if curl_res.exit_status == 0 and code_str in ["200", "201", "204", "301", "302"]:
                            add_log("INFO", f"Health check passed: HTTP status {code_str}")
                        else:
                            add_log("ERROR", f"Health check failed: HTTP returned code {code_str}")
                            return DeploymentExecutionResult(
                                success=False,
                                status="FAILED",
                                message="HTTP health check gagal.",
                                error_message=f"HTTP status code {code_str}",
                                logs=logs,
                            )
                    else:
                        add_log("INFO", "Health check selesai.")

            add_log("INFO", "Seluruh tahapan deployment berhasil diselesaikan.")
            return DeploymentExecutionResult(
                success=True,
                status="SUCCESS",
                commit_reference=commit_ref,
                message="Deployment completed successfully.",
                logs=logs,
            )

        except (asyncio.TimeoutError, TimeoutError):
            err_msg = "Operasi deployment melebihi batas waktu (timeout)."
            add_log("ERROR", err_msg)
            return DeploymentExecutionResult(
                success=False,
                status="FAILED",
                message="Deployment timeout.",
                error_message=err_msg,
                logs=logs,
            )
        except Exception as e:
            err_msg = f"Terjadi kesalahan saat deployment: {str(e)}"
            add_log("ERROR", err_msg)
            return DeploymentExecutionResult(
                success=False,
                status="FAILED",
                message="Deployment execution error.",
                error_message=str(e),
                logs=logs,
            )
        finally:
            if conn:
                conn.close()
