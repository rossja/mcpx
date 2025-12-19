"""
Request logging middleware that dumps all incoming request information to a text file.
Captures headers, body, and all parameters for all HTTP methods.
"""
import os
import json
from datetime import datetime
from io import BytesIO
from typing import Callable
from starlette.types import ASGIApp, Receive, Scope, Send, Message
import logging

logger = logging.getLogger(__name__)

# Default log file path - can be overridden via environment variable
REQUEST_LOG_FILE = os.environ.get("REQUEST_LOG_FILE", "requests.log")


def write_to_log_file(content: str, log_file: str = None):
    """
    Append content to the log file.
    """
    file_path = log_file or REQUEST_LOG_FILE
    try:
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(content)
            f.write("\n")
    except Exception as e:
        logger.error(f"Failed to write to request log file: {e}")


def format_request_dump(
    method: str,
    path: str,
    url: str,
    headers: list,
    query_string: bytes,
    client: tuple,
    body: bytes
) -> str:
    """
    Format all request information into a human-readable string for logging.
    """
    lines = []
    timestamp = datetime.utcnow().isoformat() + "Z"
    
    # Separator and timestamp
    lines.append("=" * 80)
    lines.append(f"TIMESTAMP: {timestamp}")
    lines.append("=" * 80)
    
    # Basic request info
    lines.append(f"METHOD: {method}")
    lines.append(f"URL: {url}")
    lines.append(f"PATH: {path}")
    
    # Client info
    if client:
        lines.append(f"CLIENT IP: {client[0]}")
        lines.append(f"CLIENT PORT: {client[1]}")
    else:
        lines.append("CLIENT: Unknown")
    
    # Parse query parameters
    lines.append("")
    lines.append("-" * 40)
    lines.append("QUERY PARAMETERS:")
    lines.append("-" * 40)
    if query_string:
        try:
            from urllib.parse import parse_qs
            params = parse_qs(query_string.decode("utf-8"))
            if params:
                for key, values in params.items():
                    for value in values:
                        lines.append(f"  {key}: {value}")
            else:
                lines.append("  (none)")
        except:
            lines.append(f"  (raw): {query_string}")
    else:
        lines.append("  (none)")
    
    # Convert headers to dict for easier access
    headers_dict = {}
    for key, value in headers:
        key_str = key.decode("latin-1") if isinstance(key, bytes) else key
        value_str = value.decode("latin-1") if isinstance(value, bytes) else value
        headers_dict[key_str.lower()] = value_str
    
    # Headers
    lines.append("")
    lines.append("-" * 40)
    lines.append("HEADERS:")
    lines.append("-" * 40)
    for key, value in headers:
        key_str = key.decode("latin-1") if isinstance(key, bytes) else key
        value_str = value.decode("latin-1") if isinstance(value, bytes) else value
        # Mask sensitive headers but still show they exist
        if key_str.lower() in ("authorization", "cookie", "x-api-key"):
            lines.append(f"  {key_str}: [REDACTED - {len(value_str)} chars]")
        else:
            lines.append(f"  {key_str}: {value_str}")
    
    # Request body
    lines.append("")
    lines.append("-" * 40)
    lines.append("BODY:")
    lines.append("-" * 40)
    
    if body:
        content_type = headers_dict.get("content-type", "")
        
        # Try to pretty-print JSON
        if "application/json" in content_type:
            try:
                json_body = json.loads(body.decode("utf-8"))
                lines.append(json.dumps(json_body, indent=2))
            except (json.JSONDecodeError, UnicodeDecodeError):
                lines.append(f"  (raw bytes, {len(body)} bytes)")
                lines.append(f"  {body[:1000]!r}")  # First 1000 bytes
        
        # Form data - show as key-value pairs
        elif "application/x-www-form-urlencoded" in content_type:
            try:
                decoded = body.decode("utf-8")
                lines.append(decoded)
                # Also parse it nicely
                from urllib.parse import parse_qs
                form_data = parse_qs(decoded)
                if form_data:
                    lines.append("  Parsed form data:")
                    for key, values in form_data.items():
                        for value in values:
                            lines.append(f"    {key}: {value}")
            except UnicodeDecodeError:
                lines.append(f"  (raw bytes, {len(body)} bytes)")
        
        # Multipart form data
        elif "multipart/form-data" in content_type:
            lines.append(f"  (multipart form data, {len(body)} bytes)")
            # Try to show a preview
            try:
                preview = body[:500].decode("utf-8", errors="replace")
                lines.append(f"  Preview: {preview}...")
            except:
                pass
        
        # Other content types
        else:
            try:
                text = body.decode("utf-8")
                if len(text) > 2000:
                    lines.append(f"  (truncated to 2000 chars, total {len(text)} chars)")
                    lines.append(text[:2000])
                else:
                    lines.append(text if text else "  (empty string)")
            except UnicodeDecodeError:
                lines.append(f"  (binary data, {len(body)} bytes)")
    else:
        lines.append("  (empty)")
    
    # End separator
    lines.append("")
    lines.append("=" * 80)
    lines.append("")
    
    return "\n".join(lines)


class RequestLoggerMiddleware:
    """
    Pure ASGI middleware that logs all incoming request information to a text file.
    Uses body caching to ensure the request body remains available for downstream handlers.
    """
    
    def __init__(self, app: ASGIApp, log_file: str = None):
        self.app = app
        self.log_file = log_file or REQUEST_LOG_FILE
        logger.info(f"Request logger initialized, writing to: {self.log_file}")
    
    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            # Only log HTTP requests, pass through websocket/lifespan
            await self.app(scope, receive, send)
            return
        
        # Collect request info from scope
        method = scope.get("method", "UNKNOWN")
        path = scope.get("path", "/")
        query_string = scope.get("query_string", b"")
        headers = scope.get("headers", [])
        client = scope.get("client")
        
        # Build full URL
        scheme = scope.get("scheme", "http")
        server = scope.get("server", ("localhost", 80))
        host = server[0] if server else "localhost"
        port = server[1] if server and len(server) > 1 else 80
        
        # Try to get host from headers
        for key, value in headers:
            if key == b"host":
                host = value.decode("latin-1")
                break
        
        if query_string:
            url = f"{scheme}://{host}{path}?{query_string.decode('latin-1')}"
        else:
            url = f"{scheme}://{host}{path}"
        
        # Collect the body by wrapping receive
        body_parts = []
        
        async def receive_wrapper() -> Message:
            message = await receive()
            if message["type"] == "http.request":
                body = message.get("body", b"")
                if body:
                    body_parts.append(body)
            return message
        
        # We need to collect all body parts before logging
        # Create a receive that caches body and allows replay
        body_collected = False
        cached_body = b""
        
        async def caching_receive() -> Message:
            nonlocal body_collected, cached_body
            
            message = await receive()
            if message["type"] == "http.request":
                body = message.get("body", b"")
                more_body = message.get("more_body", False)
                cached_body += body
                
                if not more_body:
                    body_collected = True
                    # Log the request now that we have the full body
                    try:
                        request_dump = format_request_dump(
                            method=method,
                            path=path,
                            url=url,
                            headers=headers,
                            query_string=query_string,
                            client=client,
                            body=cached_body
                        )
                        write_to_log_file(request_dump, self.log_file)
                    except Exception as e:
                        logger.error(f"Error logging request: {e}")
            
            return message
        
        # For requests that might not have a body (GET, HEAD, OPTIONS)
        # we should log immediately for those
        if method in ("GET", "HEAD", "OPTIONS", "DELETE"):
            try:
                request_dump = format_request_dump(
                    method=method,
                    path=path,
                    url=url,
                    headers=headers,
                    query_string=query_string,
                    client=client,
                    body=b""
                )
                write_to_log_file(request_dump, self.log_file)
            except Exception as e:
                logger.error(f"Error logging request: {e}")
            
            await self.app(scope, receive, send)
        else:
            # For POST, PUT, PATCH etc - use caching receive
            await self.app(scope, caching_receive, send)
