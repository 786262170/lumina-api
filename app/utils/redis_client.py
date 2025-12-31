"""
Redis client for token blacklist and caching
"""
import redis
from typing import Optional
from app.config import settings
from app.utils.logger import logger

_redis_client: Optional[redis.Redis] = None


def reset_redis_client():
    """
    Reset Redis client instance (useful for testing or reconnection)
    """
    global _redis_client
    if _redis_client:
        try:
            _redis_client.close()
        except Exception:
            pass
    _redis_client = None


def get_redis_client() -> Optional[redis.Redis]:
    """
    Get Redis client instance (singleton)
    Returns None if Redis is disabled
    """
    global _redis_client
    
    if not settings.redis_enabled:
        return None
    
    # Check if existing client is still valid
    if _redis_client is not None:
        try:
            _redis_client.ping()
            return _redis_client
        except (redis.exceptions.ConnectionError, redis.exceptions.AuthenticationError):
            # Connection lost or auth failed, reset and reconnect
            logger.warning("Redis connection lost, reconnecting...")
            reset_redis_client()
    
    # Create new connection
    try:
        # Build Redis URL with password if provided
        redis_url = settings.redis_url
        
        # Check if URL already contains password (format: redis://:password@host:port/db)
        url_has_password = "://" in redis_url and "@" in redis_url.split("://")[1]
        
        # If password is provided separately and URL doesn't have password
        if settings.redis_password and not url_has_password:
            # Format: redis://:password@host:port/db
            parts = redis_url.replace("redis://", "").split("/")
            if len(parts) == 2:
                host_port = parts[0]
                db = parts[1]
                redis_url = f"redis://:{settings.redis_password}@{host_port}/{db}"
            else:
                redis_url = f"redis://:{settings.redis_password}@{parts[0]}/0"
        
        # Log connection attempt (hide password)
        safe_url = redis_url.split("@")[0] + "@***" if "@" in redis_url else redis_url
        logger.debug(f"Connecting to Redis: {safe_url}")
        
        _redis_client = redis.from_url(
            redis_url,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5
        )
        # Test connection
        _redis_client.ping()
        logger.info("Redis connection established")
        return _redis_client
    except redis.exceptions.AuthenticationError as e:
        logger.error(
            "Redis authentication failed. Please check your Redis password. "
            "You can set it in .env as REDIS_PASSWORD=your_password or include it in REDIS_URL as redis://:password@host:port/db",
            exc_info=True
        )
        reset_redis_client()
        return None
    except Exception as e:
        logger.error(f"Redis connection error: {e}", exc_info=True)
        reset_redis_client()
        return None


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

