"""Utility functions for authentication."""

import secrets
import hashlib
import base64
import logging
from datetime import datetime, timedelta, UTC
from typing import Optional, Dict, Any

import bcrypt
import jwt

from ..config import config

logger = logging.getLogger(__name__)


def hash_password(password: str) -> str:
    """Hash a password using bcrypt with cost factor 12."""
    salt = bcrypt.gensalt(rounds=12)
    password_hash = bcrypt.hashpw(password.encode('utf-8'), salt)
    return password_hash.decode('utf-8')


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against its hash."""
    try:
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        return False


def generate_random_token(length: int = 32) -> str:
    """Generate a random token."""
    return secrets.token_urlsafe(length)


def create_access_token(user_id: int, username: str) -> str:
    """Create a JWT access token."""
    expires_at = datetime.now(UTC) + timedelta(minutes=config.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    
    payload = {
        "sub": str(user_id),
        "username": username,
        "type": "access",
        "exp": expires_at,
        "iat": datetime.now(UTC),
    }
    
    token = jwt.encode(payload, config.JWT_SECRET_KEY, algorithm=config.JWT_ALGORITHM)
    return token


def create_refresh_token(user_id: int, username: str) -> str:
    """Create a JWT refresh token."""
    expires_at = datetime.now(UTC) + timedelta(days=config.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    
    payload = {
        "sub": str(user_id),
        "username": username,
        "type": "refresh",
        "exp": expires_at,
        "iat": datetime.now(UTC),
    }
    
    token = jwt.encode(payload, config.JWT_SECRET_KEY, algorithm=config.JWT_ALGORITHM)
    return token


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify a JWT token and return its payload."""
    try:
        payload = jwt.decode(token, config.JWT_SECRET_KEY, algorithms=[config.JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("Token has expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {e}")
        return None


def generate_auth_code() -> str:
    """Generate a random authorization code."""
    return generate_random_token(32)


def verify_code_challenge(code_verifier: str, code_challenge: str, method: str = "S256") -> bool:
    """Verify a PKCE code challenge."""
    if method == "S256":
        # SHA256 hash of the verifier
        verifier_hash = hashlib.sha256(code_verifier.encode('utf-8')).digest()
        # Base64 URL-safe encode
        computed_challenge = base64.urlsafe_b64encode(verifier_hash).decode('utf-8').rstrip('=')
        return computed_challenge == code_challenge
    elif method == "plain":
        return code_verifier == code_challenge
    else:
        logger.error(f"Unsupported code challenge method: {method}")
        return False


def generate_state() -> str:
    """Generate a random state parameter for CSRF protection."""
    return generate_random_token(32)

