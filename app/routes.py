import asyncio
from pathlib import Path
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.templating import Jinja2Templates
from app.auth import create_token
from app.config import settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
async def get_ui(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

@router.post("/token")
async def login_for_access_token(request: Request):
    if settings.AUTH_MODE != "oauth2":
         raise HTTPException(status_code=400, detail="OAuth2 not enabled")
    
    # Handle both JSON and Form Data (as per OAuth2 spec, it should be Form Data)
    content_type = request.headers.get("content-type", "")
    
    client_id = None
    client_secret = None
    scope = None
    grant_type = None
    
    if "application/json" in content_type:
        try:
            body = await request.json()
            client_id = body.get("client_id")
            client_secret = body.get("client_secret")
            scope = body.get("scope")
            grant_type = body.get("grant_type")
        except:
            pass
    elif "application/x-www-form-urlencoded" in content_type:
        form = await request.form()
        client_id = form.get("client_id")
        client_secret = form.get("client_secret")
        scope = form.get("scope")
        grant_type = form.get("grant_type")
    
    # Default check for client_credentials grant type if provided
    if grant_type and grant_type != "client_credentials":
        raise HTTPException(status_code=400, detail="Unsupported grant_type")

    # Check against env vars if set
    expected_id = settings.OAUTH_CLIENT_ID
    expected_secret = settings.OAUTH_CLIENT_SECRET
    
    if expected_id and client_id != expected_id:
        raise HTTPException(status_code=401, detail="invalid_client")
    if expected_secret and client_secret != expected_secret:
        raise HTTPException(status_code=401, detail="invalid_client")
        
    if not client_id or not client_secret:
         raise HTTPException(status_code=401, detail="invalid_client")

    # Generate token
    token_data = {"sub": client_id}
    if scope:
        token_data["scope"] = scope
        
    access_token = create_token(data=token_data)
    
    return {
        "access_token": access_token, 
        "token_type": "Bearer",
        "expires_in": 3600,
        "scope": scope or ""
    }


@router.get("/logs", response_class=HTMLResponse)
async def get_logs_page(request: Request):
    """View the request log file with styled UI."""
    log_file = Path(settings.REQUEST_LOG_FILE)
    
    if not log_file.exists():
        log_content = "[ AWAITING TRANSMISSIONS ]\n\nNo requests logged yet.\nLog file will be created when the first request is received."
    else:
        try:
            content = log_file.read_text(encoding="utf-8")
            log_content = content if content.strip() else "[ LOG FILE EMPTY ]"
        except Exception as e:
            log_content = f"[ ERROR READING LOG FILE ]\n\n{e}"
    
    return templates.TemplateResponse(
        request=request,
        name="logs.html",
        context={"log_content": log_content}
    )


@router.get("/logs/raw", response_class=PlainTextResponse)
async def get_logs_raw():
    """Get raw log file contents (for auto-refresh)."""
    log_file = Path(settings.REQUEST_LOG_FILE)
    
    if not log_file.exists():
        return PlainTextResponse(
            content="[ AWAITING TRANSMISSIONS ]\n\nNo requests logged yet.",
            status_code=200
        )
    
    try:
        content = log_file.read_text(encoding="utf-8")
        if not content.strip():
            return PlainTextResponse(content="[ LOG FILE EMPTY ]", status_code=200)
        return PlainTextResponse(content=content, status_code=200)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading log file: {e}")
