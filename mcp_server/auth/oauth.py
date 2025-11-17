"""OAuth 2.0 implementation for MCPX server."""

import logging
from datetime import datetime, timedelta
from typing import Optional
from urllib.parse import urlencode, parse_qs

from fastapi import APIRouter, Request, Form, HTTPException, Depends, status
from fastapi.responses import RedirectResponse, JSONResponse, HTMLResponse
from pydantic import BaseModel

from ..config import config
from .database import (
    get_user_by_username,
    update_last_login,
    save_auth_code,
    get_auth_code,
    mark_auth_code_used,
    save_tokens,
    get_refresh_token_info,
    revoke_token,
    revoke_refresh_token,
)
from .utils import (
    verify_password,
    generate_auth_code,
    verify_code_challenge,
    create_access_token,
    create_refresh_token,
    verify_token,
)

logger = logging.getLogger(__name__)

# Create OAuth router (no prefix - will be added when mounting)
oauth_router = APIRouter(tags=["oauth"])


# Pydantic models
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in: int
    refresh_token: str


class TokenRequest(BaseModel):
    grant_type: str
    code: Optional[str] = None
    redirect_uri: Optional[str] = None
    client_id: Optional[str] = None
    code_verifier: Optional[str] = None
    refresh_token: Optional[str] = None


class UserInfo(BaseModel):
    sub: str
    username: str


# Login page HTML template
LOGIN_PAGE_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>MCPX - Login</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }}
        .login-container {{
            background: white;
            padding: 2rem;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            width: 100%;
            max-width: 400px;
        }}
        h1 {{
            margin: 0 0 1.5rem 0;
            color: #333;
            font-size: 1.5rem;
            text-align: center;
        }}
        .form-group {{
            margin-bottom: 1rem;
        }}
        label {{
            display: block;
            margin-bottom: 0.5rem;
            color: #555;
            font-weight: 500;
        }}
        input {{
            width: 100%;
            padding: 0.75rem;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 1rem;
            box-sizing: border-box;
        }}
        input:focus {{
            outline: none;
            border-color: #667eea;
        }}
        button {{
            width: 100%;
            padding: 0.75rem;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 4px;
            font-size: 1rem;
            font-weight: 500;
            cursor: pointer;
            transition: background 0.2s;
        }}
        button:hover {{
            background: #5568d3;
        }}
        .error {{
            color: #e53e3e;
            font-size: 0.875rem;
            margin-top: 0.5rem;
            text-align: center;
        }}
        .info {{
            color: #718096;
            font-size: 0.875rem;
            margin-top: 1rem;
            text-align: center;
        }}
    </style>
</head>
<body>
    <div class="login-container">
        <h1>🔐 MCPX Login</h1>
        <form method="post" action="/mcp/oauth/authorize">
            <input type="hidden" name="response_type" value="{response_type}">
            <input type="hidden" name="client_id" value="{client_id}">
            <input type="hidden" name="redirect_uri" value="{redirect_uri}">
            <input type="hidden" name="state" value="{state}">
            <input type="hidden" name="code_challenge" value="{code_challenge}">
            <input type="hidden" name="code_challenge_method" value="{code_challenge_method}">
            
            <div class="form-group">
                <label for="username">Username</label>
                <input type="text" id="username" name="username" required autofocus>
            </div>
            
            <div class="form-group">
                <label for="password">Password</label>
                <input type="password" id="password" name="password" required>
            </div>
            
            <button type="submit">Login</button>
            
            {error_message}
            
            <div class="info">
                Default credentials:<br>
                Username: mcpuser<br>
                Password: OMG!letmein
            </div>
        </form>
    </div>
</body>
</html>
"""


@oauth_router.get("/authorize", response_class=HTMLResponse)
async def authorize_get(
    request: Request,
    response_type: str,
    client_id: str,
    redirect_uri: str,
    state: str,
    code_challenge: str,
    code_challenge_method: str = "S256"
):
    """OAuth 2.0 authorization endpoint (GET) - shows login page."""
    
    # Validate parameters
    if response_type != "code":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported response_type. Only 'code' is supported."
        )
    
    if code_challenge_method not in ["S256", "plain"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported code_challenge_method. Only 'S256' and 'plain' are supported."
        )
    
    # Show login page
    html_content = LOGIN_PAGE_HTML.format(
        response_type=response_type,
        client_id=client_id,
        redirect_uri=redirect_uri,
        state=state,
        code_challenge=code_challenge,
        code_challenge_method=code_challenge_method,
        error_message=""
    )
    
    return HTMLResponse(content=html_content)


@oauth_router.post("/authorize")
async def authorize_post(
    request: Request,
    response_type: str = Form(...),
    client_id: str = Form(...),
    redirect_uri: str = Form(...),
    state: str = Form(...),
    code_challenge: str = Form(...),
    code_challenge_method: str = Form("S256"),
    username: str = Form(...),
    password: str = Form(...)
):
    """OAuth 2.0 authorization endpoint (POST) - handles login."""
    
    # Validate credentials
    user = get_user_by_username(username)
    if not user or not verify_password(password, user["password_hash"]):
        # Show login page with error
        html_content = LOGIN_PAGE_HTML.format(
            response_type=response_type,
            client_id=client_id,
            redirect_uri=redirect_uri,
            state=state,
            code_challenge=code_challenge,
            code_challenge_method=code_challenge_method,
            error_message='<div class="error">Invalid username or password</div>'
        )
        return HTMLResponse(content=html_content, status_code=401)
    
    # Update last login
    update_last_login(user["id"])
    
    # Generate authorization code
    auth_code = generate_auth_code()
    expires_at = datetime.utcnow() + timedelta(minutes=config.OAUTH_AUTHORIZATION_CODE_EXPIRE_MINUTES)
    
    # Save authorization code
    save_auth_code(
        code=auth_code,
        user_id=user["id"],
        client_id=client_id,
        redirect_uri=redirect_uri,
        code_challenge=code_challenge,
        code_challenge_method=code_challenge_method,
        expires_at=expires_at
    )
    
    logger.info(f"User '{username}' authorized, generating authorization code")
    
    # Redirect back with authorization code
    params = {
        "code": auth_code,
        "state": state
    }
    redirect_url = f"{redirect_uri}?{urlencode(params)}"
    
    return RedirectResponse(url=redirect_url, status_code=302)


@oauth_router.post("/token", response_model=TokenResponse)
async def token(
    grant_type: str = Form(...),
    code: Optional[str] = Form(None),
    redirect_uri: Optional[str] = Form(None),
    client_id: Optional[str] = Form(None),
    code_verifier: Optional[str] = Form(None),
    refresh_token: Optional[str] = Form(None)
):
    """OAuth 2.0 token endpoint."""
    
    if grant_type == "authorization_code":
        # Exchange authorization code for tokens
        if not all([code, redirect_uri, client_id, code_verifier]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing required parameters"
            )
        
        # Get authorization code
        auth_code_data = get_auth_code(code)
        if not auth_code_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid authorization code"
            )
        
        # Check if code is already used
        if auth_code_data["used"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Authorization code already used"
            )
        
        # Check if code is expired
        expires_at = datetime.fromisoformat(auth_code_data["expires_at"])
        if datetime.utcnow() > expires_at:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Authorization code expired"
            )
        
        # Verify redirect URI
        if redirect_uri != auth_code_data["redirect_uri"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid redirect_uri"
            )
        
        # Verify client ID
        if client_id != auth_code_data["client_id"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid client_id"
            )
        
        # Verify code challenge
        if not verify_code_challenge(
            code_verifier,
            auth_code_data["code_challenge"],
            auth_code_data["code_challenge_method"]
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid code_verifier"
            )
        
        # Mark code as used
        mark_auth_code_used(code)
        
        # Get user
        from .database import get_user_by_id
        user = get_user_by_id(auth_code_data["user_id"])
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User not found"
            )
        
        # Generate tokens
        access_token = create_access_token(user["id"], user["username"])
        refresh_token_str = create_refresh_token(user["id"], user["username"])
        
        # Save tokens to database
        access_expires_at = datetime.utcnow() + timedelta(minutes=config.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        refresh_expires_at = datetime.utcnow() + timedelta(days=config.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
        save_tokens(
            user_id=user["id"],
            access_token=access_token,
            refresh_token=refresh_token_str,
            access_token_expires_at=access_expires_at,
            refresh_token_expires_at=refresh_expires_at
        )
        
        logger.info(f"Issued tokens for user '{user['username']}'")
        
        return TokenResponse(
            access_token=access_token,
            token_type="Bearer",
            expires_in=config.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            refresh_token=refresh_token_str
        )
    
    elif grant_type == "refresh_token":
        # Refresh access token
        if not refresh_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing refresh_token"
            )
        
        # Verify refresh token
        token_payload = verify_token(refresh_token)
        if not token_payload or token_payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Check if token is revoked
        token_info = get_refresh_token_info(refresh_token)
        if not token_info:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token not found or revoked"
            )
        
        # Get user
        from .database import get_user_by_id
        user_id = int(token_payload["sub"])
        user = get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User not found"
            )
        
        # Generate new tokens
        access_token = create_access_token(user["id"], user["username"])
        new_refresh_token = create_refresh_token(user["id"], user["username"])
        
        # Revoke old refresh token
        revoke_refresh_token(refresh_token)
        
        # Save new tokens to database
        access_expires_at = datetime.utcnow() + timedelta(minutes=config.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        refresh_expires_at = datetime.utcnow() + timedelta(days=config.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
        save_tokens(
            user_id=user["id"],
            access_token=access_token,
            refresh_token=new_refresh_token,
            access_token_expires_at=access_expires_at,
            refresh_token_expires_at=refresh_expires_at
        )
        
        logger.info(f"Refreshed tokens for user '{user['username']}'")
        
        return TokenResponse(
            access_token=access_token,
            token_type="Bearer",
            expires_in=config.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            refresh_token=new_refresh_token
        )
    
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported grant_type: {grant_type}"
        )


@oauth_router.post("/revoke")
async def revoke(
    token: str = Form(...),
    token_type_hint: Optional[str] = Form(None)
):
    """OAuth 2.0 token revocation endpoint."""
    
    # Revoke the token
    if token_type_hint == "refresh_token":
        revoke_refresh_token(token)
    else:
        # Try both
        revoke_token(token)
        revoke_refresh_token(token)
    
    logger.info("Token revoked")
    
    return JSONResponse(content={"status": "success"})


@oauth_router.get("/userinfo", response_model=UserInfo)
async def userinfo(request: Request):
    """OAuth 2.0 userinfo endpoint."""
    
    # Get token from Authorization header
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header"
        )
    
    token = auth_header.replace("Bearer ", "")
    
    # Verify token
    token_payload = verify_token(token)
    if not token_payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    return UserInfo(
        sub=token_payload["sub"],
        username=token_payload["username"]
    )

