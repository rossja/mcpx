"""Main entry point for MCPX HTTP MCP Server."""

import logging
from .server import get_server
from .config import config

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    """Run the MCPX server."""
    logger.info(f"Starting MCPX server on {config.HOST}:{config.PORT}")
    logger.info(f"Server name: {config.SERVER_NAME}")
    logger.info(f"Authentication mode: {config.AUTH_MODE}")
    
    # Initialize authentication if in OAuth mode
    if config.AUTH_MODE == "oauth":
        from .auth.database import init_database, create_default_user
        logger.info("Initializing authentication database...")
        init_database()
        create_default_user()
        logger.info("Authentication initialized successfully")
    
    # Get the server instance
    mcp = get_server()
    
    # Run the server with uvicorn
    import uvicorn
    uvicorn.run(
        mcp.streamable_http_app(),
        host=config.HOST,
        port=config.PORT,
        log_level=config.LOG_LEVEL.lower(),
    )


if __name__ == "__main__":
    main()

