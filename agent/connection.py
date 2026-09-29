import asyncio
import json
import logging
from typing import Optional
import websockets
from agent.config import AgentConfig
from agent.dispatcher import AgentLocalDispatcher

logger = logging.getLogger(__name__)


class AgentConnection:
    """Manages persistent outbound WebSocket connection to the backend control plane."""

    def __init__(self, config: AgentConfig, dispatcher: Optional[AgentLocalDispatcher] = None):
        self.config = config
        self.dispatcher = dispatcher or AgentLocalDispatcher()
        self._running = False
        self._ws = None

    async def start(self) -> None:
        self._running = True
        backoff = 1.0
        max_backoff = 30.0

        while self._running:
            ws_url = f"{self.config.ws_url}?agent_id={self.config.agent_id}&agent_token={self.config.agent_token}"
            try:
                logger.info("Connecting outbound to control plane: %s", self.config.ws_url)
                async with websockets.connect(ws_url, ping_interval=20, ping_timeout=15) as ws:
                    self._ws = ws
                    backoff = 1.0
                    logger.info("Outbound connection established successfully.")

                    # Start heartbeat task
                    heartbeat_task = asyncio.create_task(self._heartbeat_loop(ws))

                    try:
                        async for message in ws:
                            try:
                                data = json.loads(message)
                                msg_type = data.get("type")

                                if msg_type == "JOB_REQUEST":
                                    result = self.dispatcher.handle_job(data)
                                    await ws.send(json.dumps(result))
                            except Exception as ex:
                                logger.error("Error processing incoming message: %s", ex)
                    finally:
                        heartbeat_task.cancel()

            except Exception as e:
                logger.warning("Connection lost (%s). Reconnecting in %.1fs...", e, backoff)
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2.0, max_backoff)

    async def _heartbeat_loop(self, ws) -> None:
        while self._running:
            try:
                await asyncio.sleep(self.config.heartbeat_interval_seconds)
                msg = {
                    "type": "HEARTBEAT",
                    "agent_version": "1.0.0",
                }
                await ws.send(json.dumps(msg))
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning("Heartbeat send error: %s", e)
                break

    def stop(self) -> None:
        self._running = False
