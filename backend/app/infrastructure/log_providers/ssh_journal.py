import asyncio
from datetime import datetime, timezone
import json
import logging
import re
from typing import Dict, List, Optional
import asyncssh

from app.core.config import settings
from app.infrastructure.log_providers.base import (
    LogProvider,
    LogQueryResult,
    RawLogEntry,
)
from app.services.redaction import secret_redactor

logger = logging.getLogger(__name__)

SERVICE_NAME_PATTERN = re.compile(r"^[A-Za-z0-9_.@:-]+\.service$")

SINCE_MAP = {
    "5m": "5 minutes ago",
    "10m": "10 minutes ago",
    "30m": "30 minutes ago",
    "1h": "1 hour ago",
    "6h": "6 hours ago",
    "12h": "12 hours ago",
    "24h": "24 hours ago",
}

PRIORITY_MAP: Dict[str, str] = {
    "0": "EMERGENCY",
    "1": "ALERT",
    "2": "CRITICAL",
    "3": "ERROR",
    "4": "WARNING",
    "5": "NOTICE",
    "6": "INFO",
    "7": "DEBUG",
}


class SSHJournalLogProvider(LogProvider):
    """Systemd journal logs retrieval provider over SSH."""

    def __init__(
        self,
        connect_timeout: int = settings.LOG_CONNECTION_TIMEOUT,
        command_timeout: int = settings.LOG_COMMAND_TIMEOUT,
        max_bytes: int = settings.MAX_LOG_RESPONSE_BYTES,
    ):
        self.connect_timeout = connect_timeout
        self.command_timeout = command_timeout
        self.max_bytes = max_bytes

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
                logger.warning("Invalid SSH private key for logs: %s", type(e).__name__)
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

    async def get_service_logs(
        self,
        host: str,
        port: int,
        username: str,
        password: Optional[str] = None,
        private_key: Optional[str] = None,
        passphrase: Optional[str] = None,
        service_name: str = "",
        lines: int = 100,
        since: Optional[str] = None,
    ) -> LogQueryResult:
        if not SERVICE_NAME_PATTERN.match(service_name):
            return LogQueryResult(
                service_name=service_name,
                lines_requested=lines,
                lines_returned=0,
                error="INVALID_SERVICE_NAME",
            )

        clamped_lines = max(10, min(lines, 1000))

        since_arg = ""
        if since and since in SINCE_MAP:
            since_val = SINCE_MAP[since]
            since_arg = f'--since "{since_val}"'

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

            # Check if journalctl is available
            check_res = await asyncio.wait_for(
                conn.run("which journalctl 2>/dev/null", check=False),
                timeout=self.command_timeout,
            )
            if check_res.exit_status != 0:
                return LogQueryResult(
                    service_name=service_name,
                    lines_requested=clamped_lines,
                    lines_returned=0,
                    systemd_supported=False,
                    error="SYSTEMD_UNAVAILABLE",
                )

            # Build command: try direct journalctl first, fallback to sudo -n if needed
            cmd = f"journalctl -u {service_name} -n {clamped_lines} {since_arg} --no-pager -o json"
            res = await asyncio.wait_for(
                conn.run(cmd, check=False),
                timeout=self.command_timeout,
            )

            if res.exit_status != 0 and "permission denied" in (res.stderr or "").lower():
                # Try sudo -n
                sudo_cmd = f"sudo -n journalctl -u {service_name} -n {clamped_lines} {since_arg} --no-pager -o json"
                res = await asyncio.wait_for(
                    conn.run(sudo_cmd, check=False),
                    timeout=self.command_timeout,
                )

            stdout_text = res.stdout or ""
            raw_lines = [l for l in stdout_text.strip().splitlines() if l.strip()]

            entries: List[RawLogEntry] = []
            total_bytes = 0
            is_truncated = False

            for line in raw_lines:
                entry = self._parse_json_line(line)
                redacted_msg = secret_redactor.redact(entry.message)
                entry.message = redacted_msg

                entry_bytes = len(redacted_msg.encode("utf-8"))
                if total_bytes + entry_bytes > self.max_bytes:
                    is_truncated = True
                    break

                total_bytes += entry_bytes
                entries.append(entry)

            return LogQueryResult(
                service_name=service_name,
                lines_requested=clamped_lines,
                lines_returned=len(entries),
                truncated=is_truncated,
                entries=entries,
            )

        except (asyncio.TimeoutError, TimeoutError):
            return LogQueryResult(
                service_name=service_name,
                lines_requested=clamped_lines,
                lines_returned=0,
                error="TIMEOUT",
            )
        except (asyncssh.PermissionDenied, OSError, asyncssh.Error, ConnectionRefusedError, ValueError) as e:
            logger.warning("SSH connection error during get_service_logs: %s", type(e).__name__)
            return LogQueryResult(
                service_name=service_name,
                lines_requested=clamped_lines,
                lines_returned=0,
                error="SSH_UNAVAILABLE",
            )
        except Exception as e:
            logger.error("Unexpected error during get_service_logs: %s", type(e).__name__)
            return LogQueryResult(
                service_name=service_name,
                lines_requested=clamped_lines,
                lines_returned=0,
                error="INTERNAL_ERROR",
            )
        finally:
            if conn:
                conn.close()

    def _parse_json_line(self, line: str) -> RawLogEntry:
        try:
            data = json.loads(line)
            if not isinstance(data, dict):
                return RawLogEntry(timestamp=None, priority="UNKNOWN", message=line)

            # 1. Timestamp
            timestamp = None
            rt_ts = data.get("__REALTIME_TIMESTAMP")
            if rt_ts:
                try:
                    micros = int(rt_ts)
                    timestamp = datetime.fromtimestamp(micros / 1_000_000.0, tz=timezone.utc)
                except Exception:
                    pass

            # 2. Priority
            raw_prio = str(data.get("PRIORITY", "6"))
            priority = PRIORITY_MAP.get(raw_prio, "INFO")

            # 3. Message
            raw_msg = data.get("MESSAGE", "")
            if isinstance(raw_msg, list):
                # Array of byte integers
                try:
                    message = bytes(raw_msg).decode("utf-8", errors="replace")
                except Exception:
                    message = str(raw_msg)
            else:
                message = str(raw_msg)

            return RawLogEntry(
                timestamp=timestamp,
                priority=priority,
                message=message,
            )
        except Exception:
            # Fallback for plain text log line
            return RawLogEntry(
                timestamp=None,
                priority="UNKNOWN",
                message=line,
            )
