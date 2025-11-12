# MCPX Authentication Guide

This guide covers the authentication features added to MCPX.

## Overview

MCPX now supports two authentication modes:

1. **noauth**: No authentication (for development/testing)
2. **oauth**: OAuth 2.0 with PKCE (for production)

## Quick Start

### Development (No Auth)

For local development and testing, you can disable authentication:

```bash
# In .env file
AUTH_MODE=noauth
```

⚠️ **Warning**: Never use noauth mode in production!

### Production (OAuth 2.0)

For production deployments, use OAuth mode:

```bash
# In .env file
AUTH_MODE=oauth
AUTH_DB_PATH=./data/auth.db
JWT_SECRET_KEY=your-super-secret-jwt-key-here
```

Generate a secure JWT secret:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Default Credentials

- **Username**: `mcpuser`
- **Password**: `OMG!letmein`

These credentials are automatically created on first startup when in OAuth mode.

## OAuth 2.0 Flow

### Step 1: Authorization Request

Client initiates the OAuth flow by redirecting the user to:

```
GET /oauth/authorize?response_type=code&client_id=mcpx-client&redirect_uri=YOUR_CALLBACK&state=RANDOM_STATE&code_challenge=CODE_CHALLENGE&code_challenge_method=S256
```

Parameters:
- `response_type`: Must be `code`
- `client_id`: Client identifier (default: `mcpx-client`)
- `redirect_uri`: Where to redirect after authorization
- `state`: Random string for CSRF protection
- `code_challenge`: PKCE code challenge (base64url(sha256(code_verifier)))
- `code_challenge_method`: Must be `S256` or `plain`

### Step 2: User Authentication

User is presented with a login form where they enter their credentials.

### Step 3: Authorization Code

After successful authentication, the server redirects back to `redirect_uri` with:

```
YOUR_CALLBACK?code=AUTHORIZATION_CODE&state=SAME_STATE
```

### Step 4: Token Exchange

Client exchanges the authorization code for access and refresh tokens:

```bash
curl -X POST http://localhost:8000/oauth/token \
  -d "grant_type=authorization_code" \
  -d "code=AUTHORIZATION_CODE" \
  -d "redirect_uri=YOUR_CALLBACK" \
  -d "client_id=mcpx-client" \
  -d "code_verifier=CODE_VERIFIER"
```

Response:
```json
{
  "access_token": "eyJ...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "refresh_token": "eyJ..."
}
```

### Step 5: API Calls

Use the access token in the Authorization header:

```bash
curl http://localhost:8000/mcp/v1/tools \
  -H "Authorization: Bearer ACCESS_TOKEN"
```

### Step 6: Token Refresh

When the access token expires, use the refresh token:

```bash
curl -X POST http://localhost:8000/oauth/token \
  -d "grant_type=refresh_token" \
  -d "refresh_token=REFRESH_TOKEN"
```

## PKCE (Proof Key for Code Exchange)

PKCE is required for the authorization code flow to prevent code interception attacks.

### Generate Code Verifier

```python
import secrets
code_verifier = secrets.token_urlsafe(32)
```

### Generate Code Challenge (S256)

```python
import hashlib
import base64

verifier_hash = hashlib.sha256(code_verifier.encode('utf-8')).digest()
code_challenge = base64.urlsafe_b64encode(verifier_hash).decode('utf-8').rstrip('=')
```

## Token Management

### Access Tokens

- **Lifetime**: 1 hour (configurable via `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`)
- **Format**: JWT with HS256 signature
- **Claims**: `sub` (user_id), `username`, `type`, `exp`, `iat`
- **Usage**: Include in Authorization header as `Bearer <token>`

### Refresh Tokens

- **Lifetime**: 30 days (configurable via `JWT_REFRESH_TOKEN_EXPIRE_DAYS`)
- **Format**: JWT with HS256 signature
- **Usage**: Exchange for new access token when current one expires
- **Security**: One-time use (revoked after refresh)

### Token Revocation

Revoke a token:

```bash
curl -X POST http://localhost:8000/oauth/revoke \
  -d "token=ACCESS_TOKEN_OR_REFRESH_TOKEN"
```

## Database Schema

Authentication data is stored in SQLite at `./data/auth.db`.

### Tables

#### users
- `id`: Primary key
- `username`: Unique username
- `password_hash`: bcrypt hash (cost factor 12)
- `created_at`: Creation timestamp
- `last_login`: Last login timestamp

#### oauth_tokens
- `id`: Primary key
- `user_id`: Foreign key to users
- `access_token`: JWT access token
- `refresh_token`: JWT refresh token
- `access_token_expires_at`: Expiration timestamp
- `refresh_token_expires_at`: Expiration timestamp
- `revoked`: Boolean flag
- `created_at`: Creation timestamp

#### oauth_auth_codes
- `id`: Primary key
- `code`: Authorization code
- `user_id`: Foreign key to users
- `client_id`: OAuth client ID
- `redirect_uri`: Callback URI
- `code_challenge`: PKCE challenge
- `code_challenge_method`: PKCE method
- `expires_at`: Expiration timestamp
- `used`: Boolean flag
- `created_at`: Creation timestamp

## Security Considerations

### Password Security
- Passwords are hashed using bcrypt with cost factor 12
- Never store passwords in plain text
- Default password should be changed in production

### Token Security
- JWT tokens are signed with a secret key
- Secret key should be at least 32 bytes of random data
- Tokens include expiration timestamps
- Tokens can be revoked
- Refresh tokens are single-use

### HTTPS Required
- OAuth mode should ONLY be used with HTTPS in production
- Tokens can be intercepted over HTTP
- Password can be intercepted over HTTP

### PKCE Required
- Authorization code flow requires PKCE
- Prevents code interception attacks
- Code challenge method S256 is preferred

### CSRF Protection
- State parameter is required
- Client must verify state matches

## Configuration

### Environment Variables

```bash
# Authentication mode
AUTH_MODE=oauth  # or noauth

# Database path
AUTH_DB_PATH=./data/auth.db

# JWT configuration
JWT_SECRET_KEY=your-super-secret-key-here
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
JWT_REFRESH_TOKEN_EXPIRE_DAYS=30
JWT_ALGORITHM=HS256

# OAuth configuration
OAUTH_CLIENT_ID=mcpx-client
OAUTH_AUTHORIZATION_CODE_EXPIRE_MINUTES=10
```

## Troubleshooting

### Database initialization fails

```bash
# Ensure data directory exists
mkdir -p ./data

# Check permissions
ls -la ./data

# Remove and recreate database
rm -f ./data/auth.db
uv run python -m src.main
```

### Token validation fails

1. Check if token has expired
2. Verify JWT_SECRET_KEY matches
3. Check if token was revoked
4. Ensure clock synchronization

### Login fails

1. Verify default user was created
2. Check password is correct: `OMG!letmein`
3. Check database connection
4. Review server logs

### 401 Unauthorized

1. Check Authorization header format: `Bearer <token>`
2. Verify token is valid and not expired
3. Check if token is in database
4. Verify token is not revoked

## Testing

Run authentication tests:

```bash
# Run all tests
uv run pytest tests/test_auth.py -v

# Run specific test
uv run pytest tests/test_auth.py::TestPasswordHashing -v
```

## API Reference

### OAuth Endpoints

#### GET /oauth/authorize
Shows login page for user authentication.

**Query Parameters:**
- `response_type`: Must be "code"
- `client_id`: OAuth client identifier
- `redirect_uri`: Callback URI
- `state`: CSRF token
- `code_challenge`: PKCE challenge
- `code_challenge_method`: "S256" or "plain"

#### POST /oauth/authorize
Processes login form submission.

**Form Data:**
- `username`: User's username
- `password`: User's password
- (plus all parameters from GET)

#### POST /oauth/token
Exchanges authorization code for tokens or refreshes access token.

**For authorization code:**
- `grant_type`: "authorization_code"
- `code`: Authorization code
- `redirect_uri`: Must match original
- `client_id`: Must match original
- `code_verifier`: PKCE verifier

**For refresh token:**
- `grant_type`: "refresh_token"
- `refresh_token`: Valid refresh token

#### POST /oauth/revoke
Revokes an access or refresh token.

**Form Data:**
- `token`: Token to revoke
- `token_type_hint`: "access_token" or "refresh_token" (optional)

#### GET /oauth/userinfo
Returns information about the authenticated user.

**Headers:**
- `Authorization`: Bearer token

**Response:**
```json
{
  "sub": "1",
  "username": "mcpuser"
}
```

## Examples

### Example: Complete OAuth Flow with Python

```python
import secrets
import hashlib
import base64
import requests
from urllib.parse import urlencode, urlparse, parse_qs

# Configuration
base_url = "http://localhost:8000"
client_id = "mcpx-client"
redirect_uri = "http://localhost:8080/callback"

# Step 1: Generate PKCE parameters
code_verifier = secrets.token_urlsafe(32)
verifier_hash = hashlib.sha256(code_verifier.encode('utf-8')).digest()
code_challenge = base64.urlsafe_b64encode(verifier_hash).decode('utf-8').rstrip('=')
state = secrets.token_urlsafe(32)

# Step 2: Build authorization URL
auth_params = {
    "response_type": "code",
    "client_id": client_id,
    "redirect_uri": redirect_uri,
    "state": state,
    "code_challenge": code_challenge,
    "code_challenge_method": "S256"
}
auth_url = f"{base_url}/oauth/authorize?{urlencode(auth_params)}"
print(f"Visit: {auth_url}")

# Step 3: User logs in via browser, then you get callback
# For this example, we'll simulate the POST
session = requests.Session()
response = session.post(
    f"{base_url}/oauth/authorize",
    data={
        **auth_params,
        "username": "mcpuser",
        "password": "OMG!letmein"
    },
    allow_redirects=False
)

# Extract authorization code from redirect
location = response.headers.get("Location")
callback_params = parse_qs(urlparse(location).query)
auth_code = callback_params["code"][0]
returned_state = callback_params["state"][0]

# Verify state
assert returned_state == state

# Step 4: Exchange code for tokens
token_response = requests.post(
    f"{base_url}/oauth/token",
    data={
        "grant_type": "authorization_code",
        "code": auth_code,
        "redirect_uri": redirect_uri,
        "client_id": client_id,
        "code_verifier": code_verifier
    }
)
tokens = token_response.json()
access_token = tokens["access_token"]
refresh_token = tokens["refresh_token"]

print(f"Access Token: {access_token[:20]}...")
print(f"Refresh Token: {refresh_token[:20]}...")

# Step 5: Make authenticated API call
api_response = requests.get(
    f"{base_url}/mcp/v1/tools",
    headers={"Authorization": f"Bearer {access_token}"}
)
print(f"API Response: {api_response.status_code}")

# Step 6: Refresh token
refresh_response = requests.post(
    f"{base_url}/oauth/token",
    data={
        "grant_type": "refresh_token",
        "refresh_token": refresh_token
    }
)
new_tokens = refresh_response.json()
new_access_token = new_tokens["access_token"]

print(f"New Access Token: {new_access_token[:20]}...")
```

## Migration Guide

### Upgrading from Pre-Auth Version

If you're upgrading from a version without authentication:

1. **Update dependencies:**
   ```bash
   uv sync
   ```

2. **Choose authentication mode:**
   ```bash
   # For development (no auth)
   echo "AUTH_MODE=noauth" >> .env
   
   # For production (oauth)
   echo "AUTH_MODE=oauth" >> .env
   echo "JWT_SECRET_KEY=$(python -c 'import secrets; print(secrets.token_urlsafe(32))')" >> .env
   ```

3. **Start server to initialize database:**
   ```bash
   uv run python -m src.main
   ```

4. **Update clients to use OAuth flow** (if using oauth mode)

### Switching Between Modes

You can switch between noauth and oauth modes by updating the `AUTH_MODE` environment variable:

```bash
# Switch to noauth
AUTH_MODE=noauth uv run python -m src.main

# Switch to oauth
AUTH_MODE=oauth uv run python -m src.main
```

No data is lost when switching modes. The authentication database persists.

## Best Practices

1. **Always use HTTPS in production** with OAuth mode
2. **Change the default password** after first login
3. **Use strong JWT secret keys** (32+ bytes of random data)
4. **Rotate tokens regularly** by setting appropriate expiration times
5. **Monitor authentication logs** for suspicious activity
6. **Keep dependencies up to date** for security patches
7. **Use noauth mode only in trusted environments**
8. **Implement rate limiting** on authentication endpoints (future enhancement)

## Future Enhancements

Planned authentication features:

- Multi-user support with user management
- Role-based access control (RBAC)
- OAuth 2.0 client registration
- SSO integration (SAML, OpenID Connect)
- Two-factor authentication (2FA)
- API key authentication
- Rate limiting on auth endpoints
- Audit logging
- Password reset functionality
- Account lockout after failed attempts

## Support

For authentication-related issues:

1. Check the logs: `journalctl -u mcpx.service -f`
2. Verify configuration: Review `.env` file
3. Test with noauth mode to isolate issues
4. Review this documentation
5. Check the troubleshooting section
6. Open an issue on GitHub

## License

Same as MCPX main project.

