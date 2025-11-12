"""MCP Server implementation using FastMCP."""

import logging
from mcp.server.fastmcp import FastMCP
from .config import config
from .tools import echo, get_weather, web_search, get_source_ip, get_request_info

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create FastMCP server instance
mcp = FastMCP(
    "MCPX",
    dependencies=["httpx", "openai", "python-dotenv", "bcrypt", "pyjwt"]
)


# Register tools
@mcp.tool()
async def echo_tool(message: str) -> str:
    """Echo back the input message.
    
    Args:
        message: The text to echo back
        
    Returns:
        The exact input message
    """
    logger.info(f"Echo tool called with message length: {len(message)}")
    context = mcp.get_context()
    return await echo(message, context)


@mcp.tool()
async def get_weather_tool(zip_code: str) -> str:
    """Get current weather information for a US ZIP code.
    
    Args:
        zip_code: 5-digit US ZIP code
        
    Returns:
        Weather information including temperature, conditions, and humidity
    """
    logger.info(f"Weather tool called for ZIP: {zip_code}")
    context = mcp.get_context()
    try:
        return await get_weather(zip_code, context)
    except Exception as e:
        logger.error(f"Weather tool error: {str(e)}")
        raise


@mcp.tool()
async def web_search_tool(query: str, max_results: int = 5) -> str:
    """Search the web using OpenAI.
    
    Args:
        query: Search query
        max_results: Maximum number of results (default: 5)
        
    Returns:
        Search results with titles, URLs, and snippets
    """
    logger.info(f"Web search tool called with query: {query}")
    context = mcp.get_context()
    try:
        return await web_search(query, max_results, context)
    except Exception as e:
        logger.error(f"Web search tool error: {str(e)}")
        raise


@mcp.tool()
async def get_source_ip_tool() -> str:
    """Get the source IP address of the request.
    
    Returns:
        The client's IP address
    """
    logger.info("Source IP tool called")
    context = mcp.get_context()
    return await get_source_ip(context)


@mcp.tool()
async def get_request_info_tool() -> str:
    """Get comprehensive request information.
    
    Returns:
        All available request metadata including headers and connection info
    """
    logger.info("Request info tool called")
    context = mcp.get_context()
    return await get_request_info(context)


# Health check endpoint
@mcp.tool()
async def health_check() -> str:
    """Health check endpoint for monitoring.
    
    Returns:
        Server status information
    """
    return "MCPX Server is healthy and running!"


def get_server():
    """Get the configured MCP server instance."""
    logger.info("Initializing MCPX server")
    
    # Validate configuration
    config.validate()
    
    # Get the underlying ASGI app
    app = mcp.get_asgi_app()
    
    # Add OAuth routes if in OAuth mode
    if config.AUTH_MODE == "oauth":
        from .auth.oauth import oauth_router
        from .auth.middleware import AuthenticationMiddleware
        
        logger.info("Adding OAuth routes and authentication middleware")
        
        # Include OAuth router
        app.include_router(oauth_router)
        
        # Add authentication middleware
        app.add_middleware(AuthenticationMiddleware)
        
        logger.info("OAuth authentication enabled")
    else:
        logger.warning("Running in noauth mode - authentication is DISABLED")
    
    return mcp

