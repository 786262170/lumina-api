from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer
from app.utils.jwt import verify_token, is_token_blacklisted

security = HTTPBearer()


async def verify_token_middleware(request: Request, call_next):
    """
    Middleware to verify JWT token for protected routes
    """
    # Skip authentication for public endpoints
    public_paths = [
        "/docs",
        "/openapi.json",
        "/v1/auth/send-code",
        "/v1/auth/login",
        "/v1/auth/wechat-login",
        "/v1/auth/guest",
        "/v1/subscription/plans",
        "/v1/subscription/payment-callback",
    ]
    
    if any(request.url.path.startswith(path) for path in public_paths):
        response = await call_next(request)
        return response
    
    # Check for Authorization header
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = auth_header.split(" ")[1]
    
    # Check if token is blacklisted
    if is_token_blacklisted(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify token
    payload = verify_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Add user info to request state
    request.state.user_id = payload.get("sub")
    
    response = await call_next(request)
    return response

