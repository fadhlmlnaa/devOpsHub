import os
import json
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional

DEFAULT_CONFIG_PATH = os.environ.get("DEVOPS_AGENT_CONFIG", "agent_config.json")


@dataclass
class AgentConfig:
    server_url: str = "http://127.0.0.1:8000"
    agent_id: Optional[str] = None
    agent_token: Optional[str] = None
    server_id: Optional[str] = None
    workspace_id: Optional[str] = None
    heartbeat_interval_seconds: int = 30
    log_level: str = "INFO"
    config_path: str = DEFAULT_CONFIG_PATH

    @property
    def is_enrolled(self) -> bool:
        return bool(self.agent_id and self.agent_token)

    @property
    def ws_url(self) -> str:
        base = self.server_url.rstrip("/")
        if base.startswith("https://"):
            return base.replace("https://", "wss://") + "/api/v1/agent/ws"
        elif base.startswith("http://"):
            return base.replace("http://", "ws://") + "/api/v1/agent/ws"
        return f"ws://{base}/api/v1/agent/ws"

    def save(self, path: Optional[str] = None) -> None:
        target = path or self.config_path
        os.makedirs(os.path.dirname(os.path.abspath(target)), exist_ok=True)
        data = asdict(self)
        with open(target, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    @classmethod
    def load(cls, path: Optional[str] = None) -> "AgentConfig":
        target = path or DEFAULT_CONFIG_PATH
        if not os.path.exists(target):
            return cls(config_path=target)
        try:
            with open(target, "r", encoding="utf-8") as f:
                data = json.load(f)
                return cls(**data)
        except Exception:
            return cls(config_path=target)
