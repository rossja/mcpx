"""Source IP lookup tool implementation."""

from mcp.server.fastmcp import Context
from starlette.requests import Request


async def get_source_ip(context: Context) -> str:
    """Get the source IP address of the request.

    This tool examines request headers to determine the client's IP address,
    taking into account proxy headers.

    Args:
        context: MCP context containing request information

    Returns:
        Formatted string with the client's IP address
    """
    # Access the underlying request from FastMCP context
    request = _get_request_from_context(context)

    if request is None:
        return "Unable to determine source IP: Request context not available"

    # Check X-Forwarded-For header (used by proxies)
    x_forwarded_for = request.headers.get("x-forwarded-for")
    if x_forwarded_for:
        # Take the leftmost IP (original client)
        client_ip = x_forwarded_for.split(",")[0].strip()
        return f"Your source IP address: {client_ip} (via proxy)"

    # Check X-Real-IP header
    x_real_ip = request.headers.get("x-real-ip")
    if x_real_ip:
        return f"Your source IP address: {x_real_ip} (via proxy)"

    # Fall back to direct connection IP
    if request.client:
        return f"Your source IP address: {request.client.host}"

    return "Unable to determine source IP address"


def _get_request_from_context(context: Context) -> Request | None:
    """Extract the Starlette Request object from MCP context.

    Args:
        context: MCP context

    Returns:
        Starlette Request object if available, None otherwise
    """
    try:
        # FastMCP stores the request in the context's request_context
        if hasattr(context, "request_context") and context.request_context:
            return context.request_context.get("request")
        
        # Try alternative access patterns
        if hasattr(context, "_request"):
            return context._request
            
        return None
    except Exception:
        return None

