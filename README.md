# MCPX — Adversarial MCP Server for AI Red-Teaming

A production-ready MCP (Model Context Protocol) server designed for safe adversarial testing and evaluation of AI tool integration. Built with Python, FastMCP, and modern tooling.

## Purpose

**mcpx is a controlled environment for testing how AI systems behave when connected to external tools.** The goal is to help safety teams, researchers, and platform engineers evaluate robustness, authentication flows, error handling, and edge cases in tool-augmented AI systems.

This is the foundation for building adversarial test scenarios — currently providing working utility tools that can be extended or configured to test various failure modes, security controls, and AI system behaviors.

## Features

- 🎯 **Adversarial Testing Platform**: Foundation for AI red-teaming and safety evaluation
- 🚀 **5 Utility Tools**: Echo, Weather, Web Search, IP Lookup, and Request Info
- 🔒 **HTTPS Support**: Full SSL/TLS with Let's Encrypt integration
- 🔐 **OAuth 2.0 Authentication**: Test auth flows, token management, and access control
- 📡 **Streaming HTTP**: Efficient bi-directional communication
- 🐍 **Modern Python**: Built with Python 3.12+ and uv package manager
- 🔧 **Production Ready**: nginx reverse proxy, systemd service, auto-renewal
- ✅ **Tested**: Unit tests for all tools

## Use Cases

### Safety & Red-Teaming
- Test how AI systems handle authentication failures and token expiration
- Evaluate behavior with rate-limited or slow-responding tools
- Test data handling and information disclosure scenarios
- Validate refusal behaviors and escalation flows

### Eval & Research Teams
- Build reproducible test scenarios around MCP tool interactions
- Measure AI system robustness to tool errors and edge cases
- Create benchmarks for tool integration safety
- Study model behavior with external data sources

### Platform Engineers
- Validate OAuth 2.0 client implementations
- Test MCP protocol integration and error handling
- Evaluate logging, monitoring, and observability
- Stress-test tool orchestration and sandboxing

## Tools

The server currently provides 5 utility tools that serve as the foundation for adversarial testing scenarios:

### 1. Echo (`echo`)
Simple diagnostic tool that returns the input exactly as provided. Useful for testing basic connectivity and data flow.

**Parameters:**
- `message` (string, required): The text to echo back

### 2. Weather Lookup (`get_weather`)
Retrieve current weather information for a US ZIP code. Tests external API integration and data handling.

**Parameters:**
- `zip_code` (string, required): 5-digit US ZIP code

### 3. Web Search (`web_search`)
Search the web using OpenAI's capabilities. Tests information retrieval and content handling.

**Parameters:**
- `query` (string, required): Search query
- `max_results` (integer, optional): Maximum results (default: 5)

### 4. Source IP Lookup (`get_source_ip`)
Display the client's apparent IP address. Tests request metadata exposure.

**Parameters:** None

### 5. Request Information (`get_request_info`)
Display comprehensive request metadata including headers and connection info. Tests observability and information disclosure.

**Parameters:** None

## Authentication

MCPX supports two authentication modes to accommodate different use cases:

### No Authentication (noauth)

**Use for**: Development, testing, and trusted internal networks

```bash
# In your .env file
AUTH_MODE=noauth
```

⚠️ **Warning**: This mode provides NO security. Only use in trusted environments!

### OAuth 2.0 (oauth)

**Use for**: Production deployments requiring authentication

MCPX implements OAuth 2.0 Authorization Code Flow with PKCE for secure authentication.

#### Default Credentials

- **Username**: `mcpuser`
- **Password**: `OMG!letmein`

#### Configuration

```bash
# In your .env file
AUTH_MODE=oauth
AUTH_DB_PATH=./data/auth.db
JWT_SECRET_KEY=your-super-secret-jwt-key-here
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
JWT_REFRESH_TOKEN_EXPIRE_DAYS=30
```

Generate a secure JWT secret key:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

#### OAuth Flow

1. **Authorization Request**: Client requests authorization
   ```
   GET /oauth/authorize?response_type=code&client_id=mcpx-client&redirect_uri=...&state=...&code_challenge=...&code_challenge_method=S256
   ```

2. **User Login**: User enters credentials in the login page

3. **Authorization Code**: Server redirects back with authorization code
   ```
   https://redirect_uri?code=...&state=...
   ```

4. **Token Exchange**: Client exchanges code for access token
   ```
   POST /oauth/token
   grant_type=authorization_code&code=...&redirect_uri=...&client_id=...&code_verifier=...
   ```

5. **API Access**: Use access token in Authorization header
   ```
   Authorization: Bearer <access_token>
   ```

6. **Token Refresh**: When access token expires, use refresh token
   ```
   POST /oauth/token
   grant_type=refresh_token&refresh_token=...
   ```

#### OAuth Endpoints

- `GET /oauth/authorize` - Authorization endpoint (shows login page)
- `POST /oauth/authorize` - Authorization endpoint (handles login)
- `POST /oauth/token` - Token endpoint (exchange code for tokens)
- `POST /oauth/revoke` - Revoke tokens
- `GET /oauth/userinfo` - Get user information

#### Token Management

- **Access tokens**: Valid for 1 hour (configurable)
- **Refresh tokens**: Valid for 30 days (configurable)
- **Token storage**: SQLite database
- **Token format**: JWT (HS256)
- **Security**: bcrypt password hashing (cost factor 12)

## Quick Start

### Prerequisites

- Python 3.12 or higher
- [uv](https://docs.astral.sh/uv/) package manager
- OpenAI API key (for web search tool)
- Optional: OpenWeatherMap API key (for weather tool)

### Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd mcpx
   ```

2. **Install dependencies:**
   ```bash
   uv sync
   ```

3. **Configure environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env and add your API keys
   ```

4. **Run the server:**
   ```bash
   uv run python -m mcp_server.main
   ```

The server will start on `http://localhost:8000` by default.

## Development

### Project Structure

```
mcpx/
├── pyproject.toml          # uv project configuration
├── .env.example            # Example environment variables
├── .gitignore             
├── README.md
├── AUTHENTICATION.md       # Authentication documentation
├── DEPLOYMENT.md           # Deployment guide
├── LICENSE
├── data/
│   └── auth.db             # SQLite database (created at runtime)
├── mcp_server/             # MCP server application code
│   ├── __init__.py
│   ├── main.py             # Application entry point
│   ├── config.py           # Configuration management
│   ├── server.py           # MCP server implementation
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── oauth.py        # OAuth 2.0 implementation
│   │   ├── database.py     # Database models and operations
│   │   ├── middleware.py   # Authentication middleware
│   │   └── utils.py        # Password hashing, token generation
│   └── tools/
│       ├── __init__.py
│       ├── echo.py
│       ├── weather.py
│       ├── web_search.py
│       ├── ip_lookup.py
│       └── request_info.py
├── web/                    # Web assets (marketing site, etc.)
│   └── mcpx.lol/
│       ├── index.html
│       ├── script.js
│       └── styles.css
├── tests/                  # Tests mirror mcp-server structure
│   ├── __init__.py
│   ├── test_tools.py
│   ├── test_server.py
│   └── test_auth.py        # Authentication tests
├── docs/                   # Documentation
│   └── mcpx-prd.md
└── deployment/             # Deployment configurations
    ├── nginx.conf          # nginx configuration
    ├── systemd.service     # systemd service file
    └── setup.sh            # Deployment script
```

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=mcp_server

# Run specific test file
uv run pytest tests/test_tools.py

# Run with verbose output
uv run pytest -v
```

### Adding Dependencies

```bash
# Add a runtime dependency
uv add <package-name>

# Add a development dependency
uv add --dev <package-name>

# Sync dependencies
uv sync
```

## Production Deployment

### Automated Deployment (Linux)

For a complete automated deployment on Ubuntu/Debian:

```bash
# Copy your code to /opt/mcpx
sudo cp -r . /opt/mcpx

# Run the deployment script
cd /opt/mcpx/deployment
sudo ./setup.sh
```

The script will:
- Install Python 3.12+, uv, nginx, and certbot
- Set up SSL certificates with Let's Encrypt
- Configure nginx as reverse proxy
- Create systemd service
- Start the server

### Manual Deployment

1. **Install system dependencies:**
   ```bash
   sudo apt-get update
   sudo apt-get install -y python3.12 nginx certbot python3-certbot-nginx
   ```

2. **Install uv:**
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

3. **Set up the application:**
   ```bash
   sudo mkdir -p /opt/mcpx
   sudo cp -r . /opt/mcpx
   cd /opt/mcpx
   uv sync
   ```

4. **Configure environment:**
   ```bash
   sudo cp .env.example /opt/mcpx/.env
   sudo nano /opt/mcpx/.env  # Add your API keys
   ```

5. **Obtain SSL certificate:**
   ```bash
   sudo certbot certonly --nginx -d mcpx.lol
   ```

6. **Configure nginx:**
   ```bash
   sudo cp deployment/nginx.conf /etc/nginx/sites-available/mcpx.conf
   sudo ln -s /etc/nginx/sites-available/mcpx.conf /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl restart nginx
   ```

7. **Set up systemd service:**
   ```bash
   sudo cp deployment/systemd.service /etc/systemd/system/mcpx.service
   sudo systemctl daemon-reload
   sudo systemctl enable mcpx.service
   sudo systemctl start mcpx.service
   ```

### Monitoring

```bash
# Check service status
sudo systemctl status mcpx.service

# View logs
sudo journalctl -u mcpx.service -f

# Check nginx logs
sudo tail -f /var/log/nginx/mcpx.access.log
sudo tail -f /var/log/nginx/mcpx.error.log
```

## Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `MCP_SERVER_HOST` | Server bind address | `0.0.0.0` | No |
| `MCP_SERVER_PORT` | Server port | `8000` | No |
| `MCP_SERVER_NAME` | Server domain name | `mcpx.lol` | No |
| `AUTH_MODE` | Authentication mode (`noauth` or `oauth`) | `oauth` | No |
| `AUTH_DB_PATH` | Path to SQLite auth database | `./data/auth.db` | No |
| `JWT_SECRET_KEY` | Secret key for JWT signing | (auto-generated) | No** |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | Access token expiration | `60` | No |
| `JWT_REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token expiration | `30` | No |
| `OAUTH_CLIENT_ID` | OAuth client identifier | `mcpx-client` | No |
| `OPENAI_API_KEY` | OpenAI API key | - | Yes* |
| `WEATHER_API_KEY` | Weather API key | - | No |
| `CERTBOT_EMAIL` | Email for Let's Encrypt | `admin@mcpx.lol` | No |
| `LOG_LEVEL` | Logging level | `INFO` | No |
| `LOG_FORMAT` | Log format | `json` | No |

*Required for web search tool to function  
**Strongly recommended for OAuth mode to persist tokens across restarts

### Getting API Keys

1. **OpenAI API Key:**
   - Visit https://platform.openai.com/api-keys
   - Sign up or log in
   - Create a new API key
   - Add to `.env`: `OPENAI_API_KEY=sk-...`

2. **Weather API Key (Optional):**
   - Visit https://openweathermap.org/api
   - Sign up for a free account
   - Get your API key
   - Add to `.env`: `WEATHER_API_KEY=...`

## Security

- ✅ HTTPS only (HTTP redirects to HTTPS)
- ✅ OAuth 2.0 authentication with PKCE
- ✅ JWT tokens with expiration and refresh capability
- ✅ bcrypt password hashing (cost factor 12)
- ✅ CSRF protection via state parameter
- ✅ Modern TLS 1.2+ configuration
- ✅ Security headers (HSTS, X-Frame-Options, etc.)
- ✅ Input validation on all tools
- ✅ API key management via environment variables
- ✅ Request size limits
- ✅ Timeout configurations

### Authentication Security

When using OAuth mode:
- All passwords are hashed using bcrypt with cost factor 12
- JWT tokens use HS256 algorithm (configurable to RS256)
- Access tokens expire after 1 hour (configurable)
- Refresh tokens expire after 30 days (configurable)
- PKCE (Proof Key for Code Exchange) is required for authorization code flow
- State parameter prevents CSRF attacks
- Tokens are stored securely in SQLite database
- Token revocation is supported

## Performance

- Response time: < 500ms for local tools (echo, IP lookup, request info)
- Response time: < 3s for external API calls (weather, web search)
- Supports at least 10 concurrent connections
- Streaming HTTP support for efficient communication

## Troubleshooting

### Server won't start

```bash
# Check if port 8000 is already in use
sudo lsof -i :8000

# Check service logs
sudo journalctl -u mcpx.service -n 50
```

### SSL certificate issues

```bash
# Test certificate renewal
sudo certbot renew --dry-run

# Manually renew certificate
sudo certbot renew

# Check certificate expiration
sudo certbot certificates
```

### Tools not working

1. **Web search fails:** Check that `OPENAI_API_KEY` is set correctly
2. **Weather lookup fails:** Weather API key is optional, but improves functionality
3. **IP lookup returns "Unable to determine":** Check nginx proxy headers are configured

### Authentication issues

1. **401 Unauthorized errors:**
   - Check that you're using the correct access token
   - Verify token hasn't expired (1 hour lifetime)
   - Use refresh token to get a new access token
   
2. **Login fails with "Invalid username or password":**
   - Default credentials: username `mcpuser`, password `OMG!letmein`
   - Check that authentication database was initialized

3. **Database errors:**
   ```bash
   # Check if database exists
   ls -la ./data/auth.db
   
   # If missing, restart server to initialize
   uv run python -m mcp_server.main
   ```

4. **"Token expired" errors:**
   - Use the refresh token to get a new access token
   - POST to `/oauth/token` with `grant_type=refresh_token`

5. **Switch to noauth mode for testing:**
   ```bash
   # In .env file
   AUTH_MODE=noauth
   ```
   ⚠️ Only use in development/testing!

## Safety & Ethics

**This project is explicitly scoped for defensive use:** understanding and improving the robustness of AI systems, not breaking things in production.

### What mcpx is NOT
- ❌ Not a malware distribution platform
- ❌ Not a vulnerability marketplace
- ❌ Not a way to attack real users or infrastructure

### What mcpx IS
- ✅ A controlled environment for AI safety research
- ✅ A foundation for building adversarial test scenarios
- ✅ A tool for evaluating and improving AI system robustness
- ✅ A platform for testing MCP client implementations

**Intended for:** Research teams, safety engineers, and platform developers working to make AI systems more robust and secure.

## Roadmap

Future enhancements planned:
- 🎭 Configurable adversarial behaviors (delayed responses, malformed data, etc.)
- 📦 Scenario packs for common failure modes
- 🔬 Eval harness integrations
- 📊 Built-in logging and telemetry for test scenarios
- 🧪 Additional tools designed for specific test cases

## Contributing

Contributions are welcome, especially in the areas of adversarial scenarios, safety testing, and evaluation frameworks. Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass: `uv run pytest`
5. Submit a pull request

## License

See [LICENSE](LICENSE) file for details.

## References

- [Model Context Protocol Specification](https://modelcontextprotocol.io/)
- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- [uv Documentation](https://docs.astral.sh/uv/)
- [nginx Documentation](https://nginx.org/en/docs/)
- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)

## Support

For issues, questions, or contributions, please open an issue on GitHub.

---

Built with ❤️ using Python, FastMCP, and modern tooling.
