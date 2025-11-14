"""Echo tool implementation."""

from mcp.server.fastmcp import Context


async def echo(message: str, context: Context) -> str:
    """Echo back the input message.

    This is a simple diagnostic tool to verify connectivity and request handling.

    Args:
        message: The text to echo back
        context: MCP context (unused in this tool)

    Returns:
        The exact input message
    """
    return message

