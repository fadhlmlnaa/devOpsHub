import asyncio
from datetime import datetime, timezone
import logging
import os
import shlex
from typing import Any, Callable, Dict, List, Optional
import asyncssh

from app.core.config import settings
from app.infrastructure.backup_providers.base import (
    BackupProvider,
    BackupExecutionResult,
    BackupVerificationResult,
)
from app.services.redaction import secret_redactor

logger = logging.getLogger(__name__)


class SSHBackupProvider(BackupProvider):
    """Backup provider executing controlled backup operations via SSH."""

    def __init__(
        self,
        connect_timeout: int = settings.BACKUP_CONNECTION_TIMEOUT,
        command_timeout: int = settings.BACKUP_COMMAND_TIMEOUT,
        max_duration: int = settings.BACKUP_MAX_DURATION,
        max_log_lines: int = settings.MAX_BACKUP_LOG_LINES,
        max_log_msg_len: int = settings.MAX_BACKUP_LOG_MESSAGE_LENGTH,
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
                logger.warning("Invalid SSH private key for backup: %s", type(e).__name__)
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
            dest = shlex.quote(config.destination)

            # Check destination directory / writable parent
            res = await asyncio.wait_for(
                conn.run(f"mkdir -p {dest} && test -w {dest}", check=False),
                timeout=self.command_timeout,
            )
            if res.exit_status != 0:
                # Try with sudo fallback
                res_sudo = await asyncio.wait_for(
                    conn.run(f"sudo -n mkdir -p {dest}", check=False),
                    timeout=self.command_timeout,
                )
                if res_sudo.exit_status != 0:
                    return False, f"Direktori tujuan '{config.destination}' tidak dapat diakses atau dibuat di server."

            # Check source based on type
            b_type = str(config.backup_type).upper()
            if b_type == "FILESYSTEM":
                src = shlex.quote(config.source)
                src_check = await conn.run(f"test -e {src}", check=False)
                if src_check.exit_status != 0:
                    return False, f"Source direktori filesystem '{config.source}' tidak ditemukan di server."

            elif b_type == "DOCKER_VOLUME":
                vol = shlex.quote(config.source)
                vol_check = await conn.run(f"docker volume inspect {vol} || sudo -n docker volume inspect {vol}", check=False)
                if vol_check.exit_status != 0:
                    return False, f"Docker volume '{config.source}' tidak ditemukan di server."

            elif b_type == "POSTGRESQL":
                pg_check = await conn.run("which pg_dump || which docker", check=False)
                if pg_check.exit_status != 0:
                    return False, "Perintah pg_dump atau docker tidak ditemukan pada server target."

            return True, "Validasi lingkungan backup berhasil."
        except Exception as e:
            return False, f"Gagal memvalidasi server target: {str(e)}"
        finally:
            if conn:
                conn.close()

    async def execute(
        self,
        host: str,
        port: int,
        username: str,
        password: Optional[str] = None,
        private_key: Optional[str] = None,
        passphrase: Optional[str] = None,
        config: Any = None,
        log_callback: Optional[Callable[[str, str, int, datetime], Any]] = None,
    ) -> BackupExecutionResult:
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
        try:
            add_log("INFO", f"Memulai proses backup '{config.name}' (Tipe: {config.backup_type}) pada server {host}:{port}")
            add_log("INFO", f"Menghubungkan ke SSH server sebagai user '{username}'...")

            conn = await self._create_connection(host, port, username, password, private_key, passphrase)
            add_log("INFO", "Koneksi SSH berhasil tersambung.")

            dest_dir = shlex.quote(config.destination)
            src_raw = config.source.strip()
            b_type = str(config.backup_type).upper()
            is_compressed = bool(config.is_compressed)

            # Ensure destination directory exists
            mkdir_res = await asyncio.wait_for(
                conn.run(f"mkdir -p {dest_dir} || sudo -n mkdir -p {dest_dir}", check=False),
                timeout=self.command_timeout,
            )
            if mkdir_res.exit_status != 0:
                err_msg = f"Gagal membuat direktori tujuan backup '{config.destination}'."
                add_log("ERROR", err_msg)
                return BackupExecutionResult(
                    success=False,
                    status="FAILED",
                    error_message=err_msg,
                    logs=logs,
                )

            add_log("INFO", f"Direktori tujuan tervalidasi: {config.destination}")

            # Predictable filename generation
            now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H-%M-%S")
            if b_type == "POSTGRESQL":
                ext = ".sql.gz" if is_compressed else ".sql"
                file_name = f"postgresql_{src_raw}_{now_str}{ext}"
            elif b_type == "DOCKER_VOLUME":
                ext = ".tar.gz" if is_compressed else ".tar"
                file_name = f"docker_vol_{src_raw}_{now_str}{ext}"
            else:  # FILESYSTEM
                clean_name = os.path.basename(src_raw.rstrip("/")) or "filesystem"
                ext = ".tar.gz" if is_compressed else ".tar"
                file_name = f"{clean_name}_{now_str}{ext}"

            dest_file_path = os.path.join(config.destination.rstrip("/"), file_name)
            safe_dest_file = shlex.quote(dest_file_path)

            path_env = "export PATH=$PATH:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"

            # Execute specific backup operation
            if b_type == "POSTGRESQL":
                add_log("INFO", f"Mengeksekusi PostgreSQL dump untuk database '{src_raw}'...")
                safe_db = shlex.quote(src_raw)

                if is_compressed:
                    dump_cmd = (
                        f"{path_env} && ("
                        f"pg_dump {safe_db} 2>/dev/null | gzip -c > {safe_dest_file} || "
                        f"sudo -n -u postgres pg_dump {safe_db} 2>/dev/null | gzip -c > {safe_dest_file} || "
                        f"sudo -n pg_dump {safe_db} | gzip -c > {safe_dest_file}"
                        f")"
                    )
                else:
                    dump_cmd = (
                        f"{path_env} && ("
                        f"pg_dump {safe_db} > {safe_dest_file} || "
                        f"sudo -n -u postgres pg_dump {safe_db} > {safe_dest_file} || "
                        f"sudo -n pg_dump {safe_db} > {safe_dest_file}"
                        f")"
                    )

                dump_res = await asyncio.wait_for(
                    conn.run(dump_cmd, check=False),
                    timeout=self.command_timeout,
                )

                if dump_res.exit_status != 0:
                    err_msg = dump_res.stderr.strip() if dump_res.stderr else "Gagal mengeksekusi pg_dump pada server."
                    add_log("ERROR", f"PostgreSQL dump gagal: {err_msg}")
                    return BackupExecutionResult(
                        success=False,
                        status="FAILED",
                        error_message=err_msg,
                        logs=logs,
                    )
                add_log("INFO", f"PostgreSQL dump berhasil disimpan ke {dest_file_path}")

            elif b_type == "FILESYSTEM":
                add_log("INFO", f"Mengeksekusi arsip filesystem untuk direktori '{src_raw}'...")
                safe_src = shlex.quote(src_raw)
                parent_dir = os.path.dirname(src_raw.rstrip("/")) or "/"
                base_target = os.path.basename(src_raw.rstrip("/"))

                tar_flags = "-czf" if is_compressed else "-cf"
                tar_cmd = (
                    f"{path_env} && ("
                    f"tar {tar_flags} {safe_dest_file} -C {shlex.quote(parent_dir)} {shlex.quote(base_target)} 2>/dev/null || "
                    f"sudo -n tar {tar_flags} {safe_dest_file} -C {shlex.quote(parent_dir)} {shlex.quote(base_target)}"
                    f")"
                )

                tar_res = await asyncio.wait_for(
                    conn.run(tar_cmd, check=False),
                    timeout=self.command_timeout,
                )

                if tar_res.exit_status != 0:
                    err_msg = tar_res.stderr.strip() if tar_res.stderr else "Gagal membuat arsip filesystem."
                    add_log("ERROR", f"Arsip filesystem gagal: {err_msg}")
                    return BackupExecutionResult(
                        success=False,
                        status="FAILED",
                        error_message=err_msg,
                        logs=logs,
                    )
                add_log("INFO", f"Arsip filesystem berhasil disimpan ke {dest_file_path}")

            elif b_type == "DOCKER_VOLUME":
                add_log("INFO", f"Mengeksekusi backup docker volume '{src_raw}'...")
                safe_vol = shlex.quote(src_raw)
                tar_flags = "-czf" if is_compressed else "-cf"

                # Backup docker volume using a temporary helper container mounting the volume read-only
                docker_cmd = (
                    f"{path_env} && ("
                    f"docker run --rm -v {safe_vol}:/vol_data:ro -v {dest_dir}:/backup_target alpine "
                    f"tar {tar_flags} /backup_target/{shlex.quote(file_name)} -C /vol_data . 2>/dev/null || "
                    f"sudo -n docker run --rm -v {safe_vol}:/vol_data:ro -v {dest_dir}:/backup_target alpine "
                    f"tar {tar_flags} /backup_target/{shlex.quote(file_name)} -C /vol_data ."
                    f")"
                )

                docker_res = await asyncio.wait_for(
                    conn.run(docker_cmd, check=False),
                    timeout=self.command_timeout,
                )

                if docker_res.exit_status != 0:
                    err_msg = docker_res.stderr.strip() if docker_res.stderr else "Gagal mengeksekusi backup docker volume."
                    add_log("ERROR", f"Docker volume backup gagal: {err_msg}")
                    return BackupExecutionResult(
                        success=False,
                        status="FAILED",
                        error_message=err_msg,
                        logs=logs,
                    )
                add_log("INFO", f"Docker volume backup berhasil disimpan ke {dest_file_path}")

            # Verify file created & get file size
            size_res = await asyncio.wait_for(
                conn.run(f"stat -c %s {safe_dest_file} 2>/dev/null || stat -f %z {safe_dest_file} 2>/dev/null || ls -nl {safe_dest_file} | awk '{{print $5}}'", check=False),
                timeout=self.command_timeout,
            )
            file_size = None
            if size_res.exit_status == 0 and size_res.stdout.strip().isdigit():
                file_size = int(size_res.stdout.strip())
                add_log("INFO", f"Ukuran file backup: {file_size} bytes ({file_size / (1024 * 1024):.2f} MB)")

            # Calculate SHA-256 checksum
            add_log("INFO", "Menghitung checksum SHA-256 file backup...")
            chk_res = await asyncio.wait_for(
                conn.run(f"sha256sum {safe_dest_file} 2>/dev/null | awk '{{print $1}}' || shasum -a 256 {safe_dest_file} 2>/dev/null | awk '{{print $1}}'", check=False),
                timeout=self.command_timeout,
            )
            checksum = None
            if chk_res.exit_status == 0 and chk_res.stdout.strip():
                checksum = chk_res.stdout.strip().split()[0]
                add_log("INFO", f"Checksum SHA-256: {checksum}")
            else:
                add_log("WARNING", "Peringatan: Gagal menghitung checksum SHA-256 pada server.")

            add_log("INFO", "Proses backup selesai dengan sukses.")

            return BackupExecutionResult(
                success=True,
                status="SUCCESS",
                file_name=file_name,
                file_path=dest_file_path,
                file_size_bytes=file_size,
                checksum=checksum,
                logs=logs,
            )

        except asyncio.TimeoutError:
            err_msg = f"Operasi backup melebihi batas waktu ({self.command_timeout} detik)."
            add_log("ERROR", err_msg)
            return BackupExecutionResult(
                success=False,
                status="FAILED",
                error_message=err_msg,
                logs=logs,
            )
        except Exception as e:
            err_msg = f"Terjadi kesalahan tidak terduga saat backup: {str(e)}"
            add_log("ERROR", err_msg)
            return BackupExecutionResult(
                success=False,
                status="FAILED",
                error_message=err_msg,
                logs=logs,
            )
        finally:
            if conn:
                conn.close()

    async def verify(
        self,
        host: str,
        port: int,
        username: str,
        password: Optional[str] = None,
        private_key: Optional[str] = None,
        passphrase: Optional[str] = None,
        file_path: str = "",
        expected_checksum: Optional[str] = None,
    ) -> BackupVerificationResult:
        conn = None
        try:
            conn = await self._create_connection(host, port, username, password, private_key, passphrase)
            safe_file = shlex.quote(file_path)

            # Check if file exists on server
            exist_check = await asyncio.wait_for(
                conn.run(f"test -f {safe_file} || sudo -n test -f {safe_file}", check=False),
                timeout=self.command_timeout,
            )
            if exist_check.exit_status != 0:
                return BackupVerificationResult(
                    verified=False,
                    file_exists=False,
                    stored_checksum=expected_checksum,
                    calculated_checksum=None,
                    message="File backup tidak ditemukan pada direktori server.",
                )

            # Calculate SHA-256
            chk_res = await asyncio.wait_for(
                conn.run(f"sha256sum {safe_file} 2>/dev/null | awk '{{print $1}}' || shasum -a 256 {safe_file} 2>/dev/null | awk '{{print $1}}'", check=False),
                timeout=self.command_timeout,
            )
            if chk_res.exit_status != 0 or not chk_res.stdout.strip():
                return BackupVerificationResult(
                    verified=False,
                    file_exists=True,
                    stored_checksum=expected_checksum,
                    calculated_checksum=None,
                    message="Gagal menghitung checksum file backup pada server.",
                )

            calculated = chk_res.stdout.strip().split()[0]
            if expected_checksum and calculated.lower() == expected_checksum.lower():
                return BackupVerificationResult(
                    verified=True,
                    file_exists=True,
                    stored_checksum=expected_checksum,
                    calculated_checksum=calculated,
                    message="Verifikasi berhasil. File utuh dan checksum SHA-256 cocok 100%.",
                )
            else:
                return BackupVerificationResult(
                    verified=False,
                    file_exists=True,
                    stored_checksum=expected_checksum,
                    calculated_checksum=calculated,
                    message=f"Verifikasi gagal. Checksum tidak cocok (Tersimpan: {expected_checksum}, Dihitung: {calculated}).",
                )

        except Exception as e:
            return BackupVerificationResult(
                verified=False,
                file_exists=False,
                stored_checksum=expected_checksum,
                calculated_checksum=None,
                message=f"Gagal melakukan verifikasi backup ke server: {str(e)}",
            )
        finally:
            if conn:
                conn.close()
