"""
Redis client for token blacklist and caching
"""
import redis
from typing import Optional
from app.config import settings

_redis_client: Optional[redis.Redis] = None


def get_redis_client() -> Optional[redis.Redis]:
    """
    Get Redis client instance (singleton)
    Returns None if Redis is disabled
    """
    global _redis_client
    
    if not settings.redis_enabled:
        return None
    
    if _redis_client is None:
        try:
            _redis_client = redis.from_url(
                settings.redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            # Test connection
            _redis_client.ping()
        except Exception as e:
            print(f"Redis connection error: {e}")
            return None
    
    return _redis_client


def is_redis_available() -> bool:
    """Check if Redis is available"""
    client = get_redis_client()
    if client is None:
        return False
    try:
        client.ping()
        return True
    except Exception:
        return False

