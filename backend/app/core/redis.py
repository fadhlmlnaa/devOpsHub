import logging
from typing import Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

_redis_client = None


def get_redis_client():
    """Returns a Redis client instance if available."""
    global _redis_client
    if _redis_client is None:
        try:
            import redis
            _redis_client = redis.from_url(
                settings.REDIS_URL,
                max_connections=settings.REDIS_MAX_CONNECTIONS,
                socket_timeout=3,
                decode_responses=True,
            )
        except Exception as e:
            logger.warning("Redis client initialization failed: %s", e)
            return None
    return _redis_client


def check_redis_connection() -> bool:
    """Checks whether Redis is responsive."""
    try:
        client = get_redis_client()
        if client is None:
            return False
        return bool(client.ping())
    except Exception as e:
        logger.debug("Redis ping failed: %s", e)
        return False
