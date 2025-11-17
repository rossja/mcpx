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
    
    # Determine which app to run
    if config.AUTH_MODE == "oauth" and hasattr(mcp, '_wrapper_app'):
        app = mcp._wrapper_app
        logger.info("Running with OAuth wrapper app")
    else:
        app = mcp.streamable_http_app()
        logger.info("Running standard MCP app")
    
    # Run the server with uvicorn
    import uvicorn
    uvicorn.run(
        app,
        host=config.HOST,
        port=config.PORT,
        log_level=config.LOG_LEVEL.lower(),
    )


if __name__ == "__main__":
    main()

