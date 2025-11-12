"""Authentication middleware for MCPX server."""

import logging
from typing import Optional, Callable
from datetime import datetime

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from ..config import config
from .utils import verify_token
from .database import get_token_info, get_user_by_id

logger = logging.getLogger(__name__)


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """Middleware to handle authentication based on configured mode."""
    
    def __init__(self, app, exempt_paths: Optional[list] = None):
        super().__init__(app)
        self.exempt_paths = exempt_paths or [
            "/oauth/authorize",
            "/oauth/token",
            "/oauth/revoke",
            "/docs",
            "/redoc",
            "/openapi.json",
        ]
    
    async def dispatch(self, request: Request, call_next: Callable):
        """Process the request and apply authentication if needed."""
        
        # Check if path is exempt from authentication
        if any(request.url.path.startswith(path) for path in self.exempt_paths):
            return await call_next(request)
        
        # If noauth mode, skip authentication
        if config.AUTH_MODE == "noauth":
            logger.debug(f"noauth mode: allowing request to {request.url.path}")
            return await call_next(request)
        
        # OAuth mode - require authentication
        if config.AUTH_MODE == "oauth":
            # Get token from Authorization header
            auth_header = request.headers.get("Authorization")
            
            if not auth_header:
                logger.warning(f"Missing Authorization header for {request.url.path}")
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Missing Authorization header"},
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            if not auth_header.startswith("Bearer "):
                logger.warning(f"Invalid Authorization header format for {request.url.path}")
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Invalid Authorization header format"},
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            # Extract token
            token = auth_header.replace("Bearer ", "")
            
            # Verify JWT token
            token_payload = verify_token(token)
            if not token_payload:
                logger.warning(f"Invalid or expired token for {request.url.path}")
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Invalid or expired token"},
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            # Check if token is in database and not revoked
            token_info = get_token_info(token)
            if not token_info:
                logger.warning(f"Token not found or revoked for {request.url.path}")
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Token not found or revoked"},
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            # Check token expiration from database
            expires_at = datetime.fromisoformat(token_info["access_token_expires_at"])
            if datetime.utcnow() > expires_at:
                logger.warning(f"Token expired for {request.url.path}")
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Token expired"},
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            # Get user
            user = get_user_by_id(token_info["user_id"])
            if not user:
                logger.warning(f"User not found for token for {request.url.path}")
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "User not found"},
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            # Add user info to request state
            request.state.user = user
            request.state.token_payload = token_payload
            
            logger.debug(f"Authenticated user '{user['username']}' for {request.url.path}")
        
        # Continue with the request
        response = await call_next(request)
        return response


def get_current_user(request: Request) -> Optional[dict]:
    """Get the current authenticated user from request state."""
    return getattr(request.state, "user", None)


def require_auth(request: Request) -> dict:
    """Dependency to require authentication."""
    user = get_current_user(request)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    return user

