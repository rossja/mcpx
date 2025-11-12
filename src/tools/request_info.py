"""Request information tool implementation."""

from mcp.server.fastmcp import Context
from starlette.requests import Request


async def get_request_info(context: Context) -> str:
    """Get comprehensive request information.

    Returns all available request metadata including headers, method, path, etc.

    Args:
        context: MCP context containing request information

    Returns:
        Formatted string with all request details
    """
    request = _get_request_from_context(context)

    if request is None:
        return "Unable to retrieve request information: Request context not available"

    # Build comprehensive request info
    info_parts = ["Request Information:\n"]

    # HTTP Method and Path
    info_parts.append("Basic Information:")
    info_parts.append(f"  Method: {request.method}")
    info_parts.append(f"  Path: {request.url.path}")
    info_parts.append(f"  Query String: {request.url.query or '(none)'}")
    info_parts.append(f"  Protocol: {request.scope.get('scheme', 'unknown').upper()}/{request.scope.get('http_version', '?')}")
    info_parts.append("")

    # Source IP Information
    info_parts.append("Connection:")
    if request.client:
        info_parts.append(f"  Client IP: {request.client.host}")
        info_parts.append(f"  Client Port: {request.client.port}")

    x_forwarded_for = request.headers.get("x-forwarded-for")
    if x_forwarded_for:
        info_parts.append(f"  X-Forwarded-For: {x_forwarded_for}")
        info_parts.append(f"  Original IP: {x_forwarded_for.split(',')[0].strip()}")

    x_real_ip = request.headers.get("x-real-ip")
    if x_real_ip:
        info_parts.append(f"  X-Real-IP: {x_real_ip}")

    info_parts.append("")

    # Headers
    info_parts.append("Headers:")
    for header_name, header_value in sorted(request.headers.items()):
        # Sanitize potentially sensitive headers
        if header_name.lower() in ["authorization", "cookie", "x-api-key"]:
            header_value = "[REDACTED]"
        info_parts.append(f"  {header_name}: {header_value}")

    info_parts.append("")

    # Additional metadata
    info_parts.append("Additional Metadata:")
    info_parts.append(f"  Server: {request.scope.get('server', ('unknown', 0))[0]}:{request.scope.get('server', ('unknown', 0))[1]}")
    
    # User agent details
    user_agent = request.headers.get("user-agent", "Unknown")
    info_parts.append(f"  User-Agent: {user_agent}")

    return "\n".join(info_parts)


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

