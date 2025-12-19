from fastapi import FastAPI, Request
from app.routes import router
from app.config import settings
from app.mcp_server import mcp
from app.request_logger import RequestLoggerMiddleware
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create MCP app first to use its lifespan
# We set path="/" so that the sub-app handles requests at the mount root (/mcp).
# We enable json_response=True and stateless_http=True to ensure the UI can parse the response as standard JSON.
mcp_app = mcp.http_app(path="/", json_response=True, stateless_http=True)

# Pass the MCP app's lifespan to FastAPI
app = FastAPI(title="MCP Test Server", lifespan=mcp_app.lifespan)

# Add request logging middleware (logs full request details to file)
# Log file path can be configured via REQUEST_LOG_FILE environment variable
app.add_middleware(RequestLoggerMiddleware, log_file=settings.REQUEST_LOG_FILE)

# NFR-03: Logging incoming requests
@app.middleware("http")
async def log_requests(request: Request, call_next):
    # Fix for trailing slash on /mcp endpoint to avoid 307 Redirects
    # which some MCP clients do not handle correctly.
    if request.url.path == "/mcp":
        request.scope["path"] = "/mcp/"

    # Log IP and Tool if possible
    # We can't easily parse the body here without consuming it, 
    # but we can log the path and IP.
    client_ip = request.client.host
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        client_ip = forwarded.split(",")[0]
        
    logger.info(f"Incoming request from {client_ip}: {request.method} {request.url.path}")
    
    response = await call_next(request)
    return response

app.include_router(router)

# Mount MCP Server
# The SSE transport can sometimes cause redirect loops if trailing slashes aren't handled carefully.
# FastMCP/Starlette mounting behavior can be tricky.
# We mount at /mcp, but the internal path for SSE is often /sse or /messages depending on the transport.
# The fastmcp.http_app() creates an app that expects requests at its root.
# When we mount it at "/mcp", requests to "/mcp" might be redirected to "/mcp/" by Starlette if not handled,
# or vice versa.
app.mount("/mcp", mcp_app)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.PORT)
