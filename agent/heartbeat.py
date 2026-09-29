import asyncio
import logging
from agent.client import AgentClient
from agent.config import AgentConfig

logger = logging.getLogger(__name__)


class AgentHeartbeatService:
    """Fallback HTTP Heartbeat runner for environments without persistent WebSocket."""

    def __init__(self, config: AgentConfig):
        self.config = config
        self.client = AgentClient(config)
        self._running = False

    async def start(self) -> None:
        self._running = True
        logger.info("Starting fallback HTTP heartbeat loop...")
        while self._running:
            try:
                ok = await self.client.send_heartbeat_http()
                if ok:
                    logger.debug("Heartbeat acknowledged.")
                else:
                    logger.warning("Heartbeat delivery failed.")
            except Exception as e:
                logger.warning("Heartbeat error: %s", e)
            await asyncio.sleep(self.config.heartbeat_interval_seconds)

    def stop(self) -> None:
        self._running = False
