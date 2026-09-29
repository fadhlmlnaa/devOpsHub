import platform
import shutil
import os
import httpx
from typing import Dict, Any, Optional
from agent.config import AgentConfig


class AgentClient:
    """REST HTTP Client for initial enrollment and fallback communications."""

    def __init__(self, config: AgentConfig):
        self.config = config

    @staticmethod
    def detect_system_info() -> Dict[str, Any]:
        return {
            "hostname": platform.node(),
            "operating_system": f"{platform.system()} {platform.release()}",
            "architecture": platform.machine(),
            "agent_version": "1.0.0",
        }

    @staticmethod
    def detect_capabilities() -> Dict[str, bool]:
        has_systemd = os.path.exists("/run/systemd/system") or shutil.which("systemctl") is not None
        has_docker = shutil.which("docker") is not None
        has_postgres = (shutil.which("pg_dump") is not None) or (shutil.which("psql") is not None)
        return {
            "systemd": bool(has_systemd),
            "docker": bool(has_docker),
            "postgresql": bool(has_postgres),
            "filesystem_backup": True,
            "monitoring": True,
        }

    async def enroll(self, enrollment_token: str) -> Dict[str, Any]:
        url = f"{self.config.server_url.rstrip('/')}/api/v1/agent/enroll"
        sys_info = self.detect_system_info()
        capabilities = self.detect_capabilities()

        payload = {
            "enrollment_token": enrollment_token.strip(),
            "hostname": sys_info["hostname"],
            "operating_system": sys_info["operating_system"],
            "architecture": sys_info["architecture"],
            "agent_version": sys_info["agent_version"],
            "capabilities": capabilities,
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code != 200:
                error_detail = resp.text
                try:
                    error_detail = resp.json().get("detail", error_detail)
                except Exception:
                    pass
                raise ValueError(f"Enrollment gagal ({resp.status_code}): {error_detail}")

            data = resp.json()
            self.config.agent_id = data["agent_id"]
            self.config.server_id = data["server_id"]
            self.config.workspace_id = data["workspace_id"]
            self.config.agent_token = data["agent_token"]
            self.config.save()
            return data

    async def send_heartbeat_http(self) -> bool:
        if not self.config.is_enrolled:
            return False
        url = f"{self.config.server_url.rstrip('/')}/api/v1/agent/heartbeat"
        sys_info = self.detect_system_info()
        capabilities = self.detect_capabilities()

        payload = {
            "agent_id": self.config.agent_id,
            "agent_version": sys_info["agent_version"],
            "hostname": sys_info["hostname"],
            "operating_system": sys_info["operating_system"],
            "architecture": sys_info["architecture"],
            "capabilities": capabilities,
            "status": "ONLINE",
        }

        headers = {
            "X-Agent-ID": self.config.agent_id,
            "X-Agent-Token": self.config.agent_token,
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(url, json=payload, headers=headers)
                return resp.status_code == 200
        except Exception:
            return False
