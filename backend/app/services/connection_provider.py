import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Dict, Any
import asyncssh

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class ConnectionResult:
    success: bool
    message: str
    status: str  # "ONLINE", "OFFLINE", "UNKNOWN"
    server_info: Optional[Dict[str, Any]] = None


class ConnectionProvider(ABC):
    """Abstract connection provider interface.

    Allows future seamless transition from SSHProvider to AgentProvider without rewriting business logic.
    """

    @abstractmethod
    async def test_connection(
        self,
        host: str,
        port: int,
        username: str,
        password: Optional[str] = None,
        private_key: Optional[str] = None,
        passphrase: Optional[str] = None,
    ) -> ConnectionResult:
        """Tests remote server connectivity and basic command execution."""
        pass

    @abstractmethod
    async def get_server_info(
        self,
        host: str,
        port: int,
        username: str,
        password: Optional[str] = None,
        private_key: Optional[str] = None,
        passphrase: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Fetches basic server information (OS, kernel, uptime, arch)."""
        pass

    @abstractmethod
    async def collect_raw_metrics(
        self,
        host: str,
        port: int,
        username: str,
        password: Optional[str] = None,
        private_key: Optional[str] = None,
        passphrase: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Collects raw monitoring telemetry sections over a single connection session."""
        pass


class SSHProvider(ConnectionProvider):
    """Asynchronous SSH connection provider powered by AsyncSSH."""

    def __init__(
        self,
        connect_timeout: int = settings.SSH_CONNECT_TIMEOUT,
        command_timeout: int = settings.SSH_COMMAND_TIMEOUT,
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
                logger.warning("Invalid SSH private key provided: %s", type(e).__name__)
                raise ValueError("Format SSH private key tidak valid atau passphrase salah.") from e

        return await asyncio.wait_for(
            asyncssh.connect(
                host=host,
                port=port,
                username=username,
                password=password,
                client_keys=client_keys,
                known_hosts=None,  # Accept host key dynamically for management
            ),
            timeout=self.connect_timeout,
        )

    async def test_connection(
        self,
        host: str,
        port: int,
        username: str,
        password: Optional[str] = None,
        private_key: Optional[str] = None,
        passphrase: Optional[str] = None,
    ) -> ConnectionResult:
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

            # Test basic command execution
            res = await asyncio.wait_for(
                conn.run("echo ok", check=True),
                timeout=self.command_timeout,
            )

            if "ok" in res.stdout:
                # Optionally fetch basic server info
                info = await self._extract_basic_info(conn)
                return ConnectionResult(
                    success=True,
                    message="Koneksi SSH berhasil dan remote command berjalan normal.",
                    status="ONLINE",
                    server_info=info,
                )
            else:
                return ConnectionResult(
                    success=False,
                    message="Koneksi SSH terhubung tetapi eksekusi remote command tidak terduga.",
                    status="OFFLINE",
                )

        except asyncssh.PermissionDenied:
            return ConnectionResult(
                success=False,
                message="Autentikasi SSH gagal. Periksa kembali username, password, atau private key.",
                status="OFFLINE",
            )
        except (asyncio.TimeoutError, TimeoutError):
            return ConnectionResult(
                success=False,
                message=f"Koneksi SSH batas waktu (timeout {self.connect_timeout}s). Pastikan host dan port dapat dijangkau.",
                status="OFFLINE",
            )
        except (OSError, ConnectionRefusedError, asyncssh.Error) as e:
            return ConnectionResult(
                success=False,
                message="Gagal terhubung ke server SSH. Pastikan server aktif dan firewall mengizinkan port.",
                status="OFFLINE",
            )
        except ValueError as e:
            return ConnectionResult(
                success=False,
                message=str(e),
                status="OFFLINE",
            )
        except Exception as e:
            logger.error("Unexpected error during SSH connection test: %s", type(e).__name__)
            return ConnectionResult(
                success=False,
                message="Terjadi kesalahan saat menguji koneksi SSH.",
                status="OFFLINE",
            )
        finally:
            if conn:
                conn.close()

    async def get_server_info(
        self,
        host: str,
        port: int,
        username: str,
        password: Optional[str] = None,
        private_key: Optional[str] = None,
        passphrase: Optional[str] = None,
    ) -> Dict[str, Any]:
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
            return await self._extract_basic_info(conn)
        finally:
            if conn:
                conn.close()

    async def _extract_basic_info(self, conn: asyncssh.SSHClientConnection) -> Dict[str, Any]:
        info: Dict[str, Any] = {
            "hostname": None,
            "operating_system": None,
            "kernel": None,
            "architecture": None,
            "uptime": None,
        }
        try:
            # Run lightweight info gathering commands
            hostname_res = await asyncio.wait_for(conn.run("hostname", check=False), timeout=5)
            if hostname_res.exit_status == 0:
                info["hostname"] = hostname_res.stdout.strip()

            arch_res = await asyncio.wait_for(conn.run("uname -m", check=False), timeout=5)
            if arch_res.exit_status == 0:
                info["architecture"] = arch_res.stdout.strip()

            kernel_res = await asyncio.wait_for(conn.run("uname -r", check=False), timeout=5)
            if kernel_res.exit_status == 0:
                info["kernel"] = kernel_res.stdout.strip()

            uptime_res = await asyncio.wait_for(conn.run("uptime -p 2>/dev/null || uptime", check=False), timeout=5)
            if uptime_res.exit_status == 0:
                info["uptime"] = uptime_res.stdout.strip()

            os_res = await asyncio.wait_for(
                conn.run("cat /etc/os-release 2>/dev/null | grep PRETTY_NAME | cut -d= -f2 | tr -d '\"'", check=False),
                timeout=5,
            )
            if os_res.exit_status == 0 and os_res.stdout.strip():
                info["operating_system"] = os_res.stdout.strip()
            else:
                uname_s = await asyncio.wait_for(conn.run("uname -s", check=False), timeout=5)
                if uname_s.exit_status == 0:
                    info["operating_system"] = uname_s.stdout.strip()

        except Exception as e:
            logger.warning("Partial server info extraction failed: %s", type(e).__name__)

        return info

    async def collect_raw_metrics(
        self,
        host: str,
        port: int,
        username: str,
        password: Optional[str] = None,
        private_key: Optional[str] = None,
        passphrase: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Executes predefined safe batch probe commands over a single SSH connection."""
        conn = None
        connect_timeout = getattr(settings, "MONITORING_CONNECT_TIMEOUT", 5)
        command_timeout = getattr(settings, "MONITORING_COMMAND_TIMEOUT", 5)

        try:
            # Single SSH connection for all metrics
            conn = await asyncio.wait_for(
                self._create_connection(
                    host=host,
                    port=port,
                    username=username,
                    password=password,
                    private_key=private_key,
                    passphrase=passphrase,
                ),
                timeout=connect_timeout,
            )

            # Predefined safe telemetry extraction script
            batch_cmd = (
                'echo "===CPU==="; head -n 20 /proc/stat 2>/dev/null || top -l 1 -n 0 2>/dev/null\n'
                'echo "===CPUINFO==="; nproc 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || grep -c ^processor /proc/cpuinfo 2>/dev/null\n'
                'echo "===MEM==="; head -n 30 /proc/meminfo 2>/dev/null || (sysctl hw.memsize 2>/dev/null; vm_stat 2>/dev/null)\n'
                'echo "===DISK==="; df -k / 2>/dev/null\n'
                'echo "===LOAD==="; cat /proc/loadavg 2>/dev/null || sysctl -n vm.loadavg 2>/dev/null || uptime 2>/dev/null\n'
                'echo "===UPTIME==="; cat /proc/uptime 2>/dev/null || uptime 2>/dev/null\n'
                'echo "===SYSTEM==="; hostname 2>/dev/null; echo "---"; cat /etc/os-release 2>/dev/null || uname -s 2>/dev/null; echo "---"; uname -r 2>/dev/null; echo "---"; uname -m 2>/dev/null\n'
                'echo "===NET==="; ip -j addr 2>/dev/null || ip addr 2>/dev/null || ifconfig 2>/dev/null\n'
            )

            res = await asyncio.wait_for(
                conn.run(batch_cmd, check=False),
                timeout=command_timeout,
            )

            raw_output = res.stdout or ""
            sections: Dict[str, str] = {}
            current_section = None
            current_lines = []

            for line in raw_output.splitlines():
                if line.startswith("===") and line.endswith("==="):
                    if current_section:
                        sections[current_section] = "\n".join(current_lines).strip()
                    current_section = line.replace("===", "").strip()
                    current_lines = []
                else:
                    current_lines.append(line)

            if current_section:
                sections[current_section] = "\n".join(current_lines).strip()

            return {
                "success": True,
                "status": "ONLINE",
                "sections": sections,
                "error": None,
            }

        except asyncssh.PermissionDenied:
            return {
                "success": False,
                "status": "UNKNOWN",
                "sections": {},
                "error": "Autentikasi SSH ditolak (Permission Denied).",
            }
        except (asyncio.TimeoutError, TimeoutError):
            return {
                "success": False,
                "status": "OFFLINE",
                "sections": {},
                "error": f"SSH connection timeout ({connect_timeout}s). Server tidak merespons.",
            }
        except (OSError, ConnectionRefusedError, asyncssh.Error) as e:
            return {
                "success": False,
                "status": "OFFLINE",
                "sections": {},
                "error": f"Gagal terhubung ke host {host}:{port} ({type(e).__name__}).",
            }
        except Exception as e:
            logger.error("Error during raw metrics collection: %s", type(e).__name__)
            return {
                "success": False,
                "status": "UNKNOWN",
                "sections": {},
                "error": f"Terjadi kesalahan monitoring: {str(e)}",
            }
        finally:
            if conn:
                conn.close()


# Provider Factory
def get_connection_provider() -> ConnectionProvider:
    return SSHProvider()
