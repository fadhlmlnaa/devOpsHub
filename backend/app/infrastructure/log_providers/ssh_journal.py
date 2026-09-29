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

            # Build command list to try:
            # 1. sudo -n journalctl with JSON output
            # 2. direct journalctl with JSON output
            # 3. sudo -n journalctl plain text
            # 4. direct journalctl plain text

            base_name = service_name[:-8] if service_name.endswith(".service") else service_name
            unit_args = f"-u {service_name}"
            if base_name != service_name:
                unit_args += f" -u {base_name}"

            commands_to_try = [
                f"sudo -n journalctl {unit_args} -n {clamped_lines} {since_arg} --no-pager -a -o json",
                f"journalctl {unit_args} -n {clamped_lines} {since_arg} --no-pager -a -o json",
                f"sudo -n journalctl {unit_args} -n {clamped_lines} {since_arg} --no-pager -a",
                f"journalctl {unit_args} -n {clamped_lines} {since_arg} --no-pager -a",
            ]

            stdout_text = ""
            is_json_format = True

            for idx, cmd in enumerate(commands_to_try):
                try:
                    res = await asyncio.wait_for(
                        conn.run(cmd, check=False),
                        timeout=self.command_timeout,
                    )
                    out = (res.stdout or "").strip()
                    if out:
                        stdout_text = out
                        is_json_format = (idx < 2) # First 2 commands are JSON
                        break
                except Exception as e:
                    logger.debug("Command failed %s: %s", cmd, e)
                    continue

            raw_lines = [l for l in stdout_text.splitlines() if l.strip()]

            entries: List[RawLogEntry] = []
            total_bytes = 0
            is_truncated = False

            for line in raw_lines:
                if is_json_format and line.startswith("{"):
                    entry = self._parse_json_line(line)
                else:
                    entry = self._parse_plain_line(line)

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
            return self._parse_plain_line(line)

    def _parse_plain_line(self, line: str) -> RawLogEntry:
        # Detect priority keywords in message
        upper_line = line.upper()
        priority = "UNKNOWN"
        if any(w in upper_line for w in ["EMERG", "ALERT", "CRIT"]):
            priority = "CRITICAL"
        elif any(w in upper_line for w in ["ERROR", "ERR", "FAIL", "FATAL", "EXCEPTION"]):
            priority = "ERROR"
        elif any(w in upper_line for w in ["WARN", "WARNING"]):
            priority = "WARNING"
        elif "DEBUG" in upper_line:
            priority = "DEBUG"
        elif any(w in upper_line for w in ["INFO", "NOTICE"]):
            priority = "INFO"

        # Attempt to parse syslog-style timestamp (e.g. Sep 29 10:30:01) or ISO timestamp
        timestamp = None
        # ISO timestamp pattern at line start (e.g. 2026-09-29T10:30:01)
        iso_match = re.match(r"^(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?)", line)
        if iso_match:
            try:
                raw_ts = iso_match.group(1).replace(" ", "T")
                timestamp = datetime.fromisoformat(raw_ts).replace(tzinfo=timezone.utc)
            except Exception:
                pass

        return RawLogEntry(
            timestamp=timestamp,
            priority=priority,
            message=line,
        )
