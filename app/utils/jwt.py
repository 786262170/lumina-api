from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
import hashlib
from app.config import settings
from app.utils.redis_client import get_redis_client
from app.utils.logger import logger


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create JWT access token
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.jwt_access_token_expire_minutes)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt


def create_refresh_token(data: Dict[str, Any]) -> str:
    """
    Create JWT refresh token
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.jwt_refresh_token_expire_days)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify and decode JWT token
    Also checks if token is blacklisted
    """
    # First check if token is blacklisted
    if is_token_blacklisted(token):
        return None
    
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        
        # Check if user's tokens have been revoked
        user_id = payload.get("sub")
        if user_id:
            redis_client = get_redis_client()
            if redis_client:
                try:
                    revocation_key = f"blacklist:user:{user_id}"
                    revocation_time = redis_client.get(revocation_key)
                    if revocation_time:
                        # Token was issued before revocation, check timestamp
                        token_iat = payload.get("iat")
                        if token_iat and float(revocation_time) > token_iat:
                            return None
                except Exception:
                    pass  # Ignore errors, allow token
        
        return payload
    except JWTError:
        return None


def add_token_to_blacklist(token: str, expires_in_seconds: int) -> bool:
    """
    Add token to blacklist (for logout)
    
    Args:
        token: JWT token to blacklist
        expires_in_seconds: Token expiration time in seconds (from exp claim)
    
    Returns:
        True if successfully added, False otherwise
    """
    redis_client = get_redis_client()
    if redis_client is None:
        # Redis not available, skip blacklist (fallback mode)
        logger.warning("Redis is not enabled. Token blacklist will not work. Please set REDIS_ENABLED=true in .env")
        return False
    
    try:
        # Use SHA256 hash of token as key for better security and uniqueness
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        key = f"blacklist:token:{token_hash}"
        
        # Set with expiration (TTL)
        redis_client.setex(key, expires_in_seconds, "1")
        
        # Verify it was set correctly
        ttl = redis_client.ttl(key)
        if ttl > 0:
            logger.info(f"Token added to blacklist: {key[:16]}..., TTL: {ttl}s")
            return True
        else:
            logger.warning(f"Token blacklist key was set but TTL is invalid: {ttl}")
            return False
    except Exception as e:
        logger.error(f"Failed to add token to blacklist: {e}", exc_info=True)
        return False


def is_token_blacklisted(token: str) -> bool:
    """
    Check if token is blacklisted (for logout)
    
    Returns:
        True if token is blacklisted, False otherwise
    """
    redis_client = get_redis_client()
    if redis_client is None:
        # Redis not available, skip blacklist check (fallback mode)
        # In production, you might want to fail closed instead
        return False
    
    try:
        # Use SHA256 hash of token as key (same as in add_token_to_blacklist)
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        key = f"blacklist:token:{token_hash}"
        
        exists = redis_client.exists(key)
        if exists > 0:
            logger.debug(f"Token is blacklisted: {key[:16]}...")
        return exists > 0
    except Exception as e:
        logger.error(f"Failed to check token blacklist: {e}", exc_info=True)
        # On error, allow token (fail open for availability)
        return False


def revoke_user_tokens(user_id: str) -> bool:
    """
    Revoke all tokens for a user (for security purposes)
    This is a simple implementation - in production, you might want to
    track tokens per user and revoke them individually.
    
    Args:
        user_id: User ID to revoke tokens for
    
    Returns:
        True if successful, False otherwise
    """
    redis_client = get_redis_client()
    if redis_client is None:
        return False
    
    try:
        # Store user revocation timestamp
        # When verifying token, check if token was issued before revocation
        key = f"blacklist:user:{user_id}"
        redis_client.set(key, str(datetime.utcnow().timestamp()))
        # Set expiration to max token lifetime (30 days for refresh token)
        redis_client.expire(key, 30 * 24 * 60 * 60)
        logger.info(f"Revoked all tokens for user: {user_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to revoke user tokens: {e}", exc_info=True)
        return False

