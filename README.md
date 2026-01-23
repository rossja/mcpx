# MCP Test Server

This is a tool to assist with offensive security testing of MCP clients. 
It serves MCP tools over **Streamable HTTP** for remote hosting, compliant with the 2025-03-26 MCP specification.

## Default Tools

The server provides several tools out-of-the-box:

1. A basic "echo" that repeats whatever is passed as a "saythis" parameter
2. A tool that tells the requester what their source ip address appears to be
3. A tool to tell the current weather when given a postal code as a parameter

## Getting Started

### Prerequisites

- Python 3.13+
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

### Local Development

1. Clone the repository
2. Install dependencies:
   ```bash
   uv sync
   ```
3. Run the server:
   ```bash
   uv run uvicorn app.main:app --host 0.0.0.0 --port 8080
   ```

### Docker Deployment

The project includes a production-ready Dockerfile.

```bash
docker build -t mcp-test-server .
docker run -p 8080:8080 mcp-test-server
```

### Heroku Deployment

1. Create a Heroku app and set the stack to container:
   ```bash
   heroku create your-app-name --team your-team
   heroku stack:set container -a your-app-name
   ```

2. Add the Heroku git remote:
   ```bash
   heroku git:remote -a your-app-name
   ```

3. Create a `.env` file with your configuration (see `env.example`), then set the environment variables:
   ```bash
   ./set-env.sh your-app-name
   ```

4. Deploy:
   ```bash
   git push heroku main
   ```

## Configuration

The server is configured via environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `PORT` | Port to listen on | 8080 |
| `AUTH_MODE` | Authentication mode: `none`, `token`, `oauth2` | `none` |
| `AUTH_TOKEN` | Static token for `token` mode | |
| `OAUTH_CLIENT_ID` | Client ID for `oauth2` mode | |
| `OAUTH_CLIENT_SECRET` | Client Secret for `oauth2` mode (used as JWT secret) | |
| `OPENWEATHER_API_KEY` | API Key for OpenWeatherMap (for weather tool) | |

## API & Transport

This server implements the **Streamable HTTP** transport.

* **Endpoint**: `POST /mcp`
* **Protocol**: JSON-RPC 2.0
* **Supported Methods**: `initialize`, `tools/list`, `tools/call`

### Example Request

```bash
curl -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{
    "jsonrpc": "2.0", 
    "method": "tools/list", 
    "id": 1
  }'
```

## Authentication

By default the server runs in "noauth" mode. 

* **none**: No authentication is required.
* **token**: Validates `Authorization: Bearer <AUTH_TOKEN>`
* **oauth2**: Validates JWT signed with `OAUTH_CLIENT_SECRET`. Endpoint `/token` issues tokens given valid `client_id` and `client_secret`.
