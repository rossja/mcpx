from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.config import settings
import jwt
import time
from typing import Optional, Dict, Any

security = HTTPBearer(auto_error=False)

def create_token(data: Dict[str, Any], expires_in: int = 3600) -> str:
    to_encode = data.copy()
    to_encode.update({"exp": time.time() + expires_in})
    return jwt.encode(to_encode, settings.OAUTH_CLIENT_SECRET, algorithm="HS256")

async def verify_auth(credentials: Optional[HTTPAuthorizationCredentials] = Security(security)):
    mode = settings.AUTH_MODE
    
    if mode == "none":
        return True
        
    if not credentials:
        raise HTTPException(status_code=401, detail="Missing authentication credentials")
        
    token = credentials.credentials
    
    if mode == "token":
        # Simple token match
        # If AUTH_TOKEN is not set, we might want to deny or warn. 
        # But assuming it's set if mode is token.
        if token != settings.AUTH_TOKEN:
            raise HTTPException(status_code=401, detail="Invalid token")
        return True
        
    if mode == "oauth2":
        try:
            # Validate JWT
            # Using OAUTH_CLIENT_SECRET as the key
            if not settings.OAUTH_CLIENT_SECRET:
                # If secret is missing, we can't validate. 
                # Fallback or error? Error is safer.
                raise HTTPException(status_code=500, detail="OAuth configuration error")
                
            payload = jwt.decode(token, settings.OAUTH_CLIENT_SECRET, algorithms=["HS256"])
            return payload
        except jwt.ExpiredSignatureError:
             raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")
            
    return True

