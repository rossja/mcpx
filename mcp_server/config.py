"""Configuration management for MCPX server."""

import os
import secrets
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Configuration class for MCPX server."""

    # Server Configuration
    HOST: str = os.getenv("MCP_SERVER_HOST", "0.0.0.0")
    PORT: int = int(os.getenv("MCP_SERVER_PORT", "8000"))
    SERVER_NAME: str = os.getenv("MCP_SERVER_NAME", "mcpx.lol")

    # Authentication Configuration
    AUTH_MODE: str = os.getenv("AUTH_MODE", "oauth")  # Options: noauth, oauth
    AUTH_DB_PATH: str = os.getenv("AUTH_DB_PATH", "./data/auth.db")
    
    # Generate a random secret key if not provided (for JWT signing)
    _jwt_secret = os.getenv("JWT_SECRET_KEY")
    JWT_SECRET_KEY: str = _jwt_secret if _jwt_secret else secrets.token_urlsafe(32)
    
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "60")
    )
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = int(
        os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "30")
    )
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    
    # OAuth Configuration
    OAUTH_CLIENT_ID: str = os.getenv("OAUTH_CLIENT_ID", "mcpx-client")
    OAUTH_AUTHORIZATION_CODE_EXPIRE_MINUTES: int = int(
        os.getenv("OAUTH_AUTHORIZATION_CODE_EXPIRE_MINUTES", "10")
    )

    # API Keys
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    WEATHER_API_KEY: Optional[str] = os.getenv("WEATHER_API_KEY")

    # SSL Configuration
    CERTBOT_EMAIL: Optional[str] = os.getenv("CERTBOT_EMAIL", "admin@mcpx.lol")

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = os.getenv("LOG_FORMAT", "json")

    @classmethod
    def validate(cls) -> bool:
        """Validate required configuration values."""
        warnings = []
        
        # Check API keys
        if not cls.OPENAI_API_KEY:
            warnings.append("WARNING: OPENAI_API_KEY not set. web_search tool will not work.")
        
        # Check authentication mode
        if cls.AUTH_MODE not in ["noauth", "oauth"]:
            print(f"ERROR: Invalid AUTH_MODE '{cls.AUTH_MODE}'. Must be 'noauth' or 'oauth'.")
            return False
            
        if cls.AUTH_MODE == "noauth":
            warnings.append("WARNING: Running in noauth mode. This is NOT secure for production!")
        
        # Check JWT secret key
        if cls.AUTH_MODE == "oauth" and not os.getenv("JWT_SECRET_KEY"):
            warnings.append("WARNING: JWT_SECRET_KEY not set. Using randomly generated key (will invalidate tokens on restart).")
        
        # Print all warnings
        for warning in warnings:
            print(warning)
        
        return True


# Create a singleton instance
config = Config()

