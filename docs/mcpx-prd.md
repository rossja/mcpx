# Product Requirements Document: MCPX HTTP MCP Server

## Document Information
- **Product Name**: MCPX HTTP MCP Server
- **Version**: 1.0
- **Date**: November 12, 2025
- **Author**: [Your Name]
- **Status**: Draft

## Executive Summary

This document outlines the requirements for building an MCP (Model Context Protocol) server that provides tool capabilities over HTTPS. The server will implement streamable HTTP connections, use modern Python tooling, and provide a set of initial utility tools for AI assistants.

## Product Overview

### Purpose
Create a production-ready MCP server that exposes tools via HTTPS, enabling AI assistants and other clients to access utility functions remotely over secure, streamable connections.

### Goals
- Provide a secure, production-grade MCP server accessible over HTTPS
- Implement streaming HTTP support for efficient bi-directional communication
- Create a foundation for extensible tool development
- Demonstrate best practices for MCP server deployment

### Success Criteria
- Server successfully handles MCP protocol requests over HTTPS
- All initial tools function correctly and reliably
- SSL certificates auto-renew without manual intervention
- Server can handle concurrent connections from multiple clients
- Response times meet acceptable thresholds (< 500ms for non-API tools)

## Technical Requirements

### Technology Stack

#### Core Technologies
- **Language**: Python 3.12+
- **Package Management**: uv (for all dependency management and runtime processes)
- **MCP Framework**: FastMCP or equivalent Python MCP implementation
- **Protocol**: HTTP/HTTPS with streaming support
- **Reverse Proxy**: nginx
- **SSL/TLS**: Let's Encrypt (via certbot)
- **Domain**: mcpx.lol

#### Architecture
```
Client (AI Assistant)
    ↓ HTTPS
nginx (Reverse Proxy + SSL Termination)
    ↓ HTTP
Python MCP Server (FastMCP)
    ↓
Tool Implementations
```

### Infrastructure Requirements

#### Server Configuration
- **Reverse Proxy**: nginx configured for:
  - SSL termination
  - Proxy pass to Python backend
  - WebSocket/streaming support
  - Request buffering configuration for streaming
  - Appropriate timeouts for long-running requests

#### SSL/TLS Configuration
- **Provider**: Let's Encrypt
- **Management**: certbot with auto-renewal
- **Requirements**:
  - Valid SSL certificate for mcpx.lol
  - Automatic renewal before expiration
  - Redirect HTTP to HTTPS
  - Modern TLS configuration (TLS 1.2+)

#### Python Application
- **Runtime**: Managed via uv
- **Process Management**: systemd or equivalent for production deployment
- **Port**: Internal port (e.g., 8000) proxied by nginx
- **Streaming**: Support for HTTP streaming responses

### Dependency Management

All Python dependencies must be managed through uv:
- `uv init` for project initialization
- `uv add <package>` for adding dependencies
- `uv run` for executing the application
- `uv sync` for dependency synchronization
- Use `pyproject.toml` for dependency declaration

## Feature Requirements

### Tool 1: Echo Service

**Purpose**: Simple diagnostic tool to verify connectivity and request handling

**Specifications**:
- **Tool Name**: `echo`
- **Description**: Returns the input exactly as provided
- **Input Parameters**:
  - `message` (string, required): The text to echo back
- **Output**: The exact input message
- **Use Cases**:
  - Connectivity testing
  - Request/response validation
  - Debugging tool chains

**Example Usage**:
```json
{
  "tool": "echo",
  "parameters": {
    "message": "Hello, MCP!"
  }
}
```

**Expected Response**:
```json
{
  "content": [
    {
      "type": "text",
      "text": "Hello, MCP!"
    }
  ]
}
```

### Tool 2: Weather Lookup

**Purpose**: Retrieve current weather information for a given location

**Specifications**:
- **Tool Name**: `get_weather`
- **Description**: Returns current weather conditions for a US ZIP code
- **Input Parameters**:
  - `zip_code` (string, required): 5-digit US ZIP code
- **Output**: Weather information including:
  - Temperature
  - Conditions (sunny, cloudy, rainy, etc.)
  - Humidity
  - Location name
- **External API**: Use a weather API (e.g., OpenWeatherMap, Weather.gov)
- **Error Handling**:
  - Invalid ZIP code format
  - ZIP code not found
  - API rate limiting
  - Network failures

**Example Usage**:
```json
{
  "tool": "get_weather",
  "parameters": {
    "zip_code": "10001"
  }
}
```

**Expected Response**:
```json
{
  "content": [
    {
      "type": "text",
      "text": "Weather for New York, NY (10001):\nTemperature: 72°F\nConditions: Partly Cloudy\nHumidity: 65%"
    }
  ]
}
```

### Tool 3: Web Search

**Purpose**: Perform web searches using OpenAI's search capabilities

**Specifications**:
- **Tool Name**: `web_search`
- **Description**: Searches the web using OpenAI's search tool and returns results
- **Input Parameters**:
  - `query` (string, required): Search query
  - `max_results` (integer, optional): Maximum number of results (default: 5)
- **Output**: Search results with:
  - Title
  - URL
  - Snippet/description
- **External API**: OpenAI API with web search enabled
- **Requirements**:
  - Valid OpenAI API key
  - Appropriate error handling for API failures
  - Rate limiting awareness

**Example Usage**:
```json
{
  "tool": "web_search",
  "parameters": {
    "query": "Model Context Protocol specification",
    "max_results": 3
  }
}
```

### Tool 4: Source IP Lookup

**Purpose**: Display the client's apparent IP address

**Specifications**:
- **Tool Name**: `get_source_ip`
- **Description**: Returns the IP address from which the request appears to originate
- **Input Parameters**: None
- **Output**: IP address information including:
  - IPv4 or IPv6 address
  - Whether behind proxy (if detectable)
- **Implementation Notes**:
  - Check X-Forwarded-For header
  - Check X-Real-IP header
  - Fall back to direct connection IP
  - Handle multiple IPs in X-Forwarded-For (take leftmost)

**Example Usage**:
```json
{
  "tool": "get_source_ip",
  "parameters": {}
}
```

**Expected Response**:
```json
{
  "content": [
    {
      "type": "text",
      "text": "Your source IP address: 203.0.113.42"
    }
  ]
}
```

### Tool 5: Request Information

**Purpose**: Display all available request metadata

**Specifications**:
- **Tool Name**: `get_request_info`
- **Description**: Returns all headers, metadata, and browser information available from the request
- **Input Parameters**: None
- **Output**: Comprehensive request information including:
  - All HTTP headers
  - Request method
  - Request path
  - Source IP (with proxy details)
  - User-Agent
  - Protocol version
  - Any other available metadata
- **Format**: Structured, readable text or JSON
- **Security Considerations**: 
  - Do not log sensitive information
  - Sanitize any potentially dangerous header values for display

**Example Usage**:
```json
{
  "tool": "get_request_info",
  "parameters": {}
}
```

**Expected Response**:
```json
{
  "content": [
    {
      "type": "text",
      "text": "Request Information:\n\nHeaders:\n  Host: mcpx.lol\n  User-Agent: Mozilla/5.0...\n  Accept: application/json\n  X-Forwarded-For: 203.0.113.42\n\nConnection:\n  Source IP: 203.0.113.42\n  Protocol: HTTP/1.1\n  Method: POST\n  Path: /mcp/v1/messages"
    }
  ]
}
```

## Non-Functional Requirements

### Performance
- **Response Time**: < 500ms for local tools (echo, IP lookup, request info)
- **Response Time**: < 3s for external API calls (weather, web search)
- **Concurrency**: Support at least 10 concurrent connections
- **Streaming**: Support streaming responses where applicable

### Reliability
- **Uptime**: Target 99% uptime
- **Error Handling**: Graceful degradation when external APIs fail
- **Logging**: Comprehensive logging of requests, errors, and system events
- **Monitoring**: Health check endpoint for monitoring systems

### Security
- **HTTPS Only**: All connections must use HTTPS
- **Certificate Management**: Automated renewal of SSL certificates
- **Input Validation**: All tool inputs must be validated
- **Rate Limiting**: Implement rate limiting to prevent abuse
- **API Key Management**: Secure storage of API keys (environment variables)
- **Header Sanitization**: Prevent header injection attacks

### Scalability
- **Horizontal Scaling**: Architecture should support multiple instances behind load balancer (future consideration)
- **Stateless Design**: Server should be stateless for easy scaling
- **Resource Management**: Appropriate timeouts and resource limits

### Maintainability
- **Code Quality**: Follow Python best practices (PEP 8)
- **Documentation**: Inline documentation and README
- **Testing**: Unit tests for tool implementations
- **Configuration**: Environment-based configuration (no hardcoded values)
- **Logging**: Structured logging for debugging and monitoring

## Configuration Requirements

### Environment Variables
```
# Server Configuration
MCP_SERVER_HOST=0.0.0.0
MCP_SERVER_PORT=8000
MCP_SERVER_NAME=mcpx.lol

# API Keys
OPENAI_API_KEY=sk-...
WEATHER_API_KEY=...

# SSL Configuration
CERTBOT_EMAIL=admin@mcpx.lol

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

### nginx Configuration Requirements
- Server block for mcpx.lol
- SSL certificate paths
- Proxy pass to localhost:8000
- Streaming support configuration
- Appropriate headers (X-Forwarded-For, X-Real-IP)
- WebSocket upgrade support (if needed)
- Request size limits
- Timeout configurations

## Development Requirements

### Project Structure
```
mcpx-server/
├── pyproject.toml          # uv project configuration
├── uv.lock                 # Dependency lock file
├── README.md               # Project documentation
├── .env.example            # Example environment variables
├── .gitignore             
├── src/
│   ├── __init__.py
│   ├── main.py             # Application entry point
│   ├── config.py           # Configuration management
│   ├── server.py           # MCP server implementation
│   └── tools/
│       ├── __init__.py
│       ├── echo.py
│       ├── weather.py
│       ├── web_search.py
│       ├── ip_lookup.py
│       └── request_info.py
├── tests/
│   ├── __init__.py
│   ├── test_tools.py
│   └── test_server.py
└── deployment/
    ├── nginx.conf          # nginx configuration
    ├── systemd.service     # systemd service file
    └── setup.sh            # Deployment script
```

### Testing Requirements
- Unit tests for each tool
- Integration tests for MCP server
- Manual testing checklist for deployment
- SSL certificate validation tests

### Documentation Requirements
- README with setup instructions
- API documentation for each tool
- Deployment guide
- Troubleshooting guide
- Configuration reference

## Deployment Requirements

### Initial Deployment Checklist
1. Set up domain DNS (mcpx.lol → server IP)
2. Install Python 3.12+
3. Install and configure uv
4. Install nginx
5. Install certbot
6. Clone repository and install dependencies
7. Configure environment variables
8. Obtain SSL certificate
9. Configure nginx
10. Start MCP server service
11. Verify all tools function correctly
12. Set up monitoring

### Maintenance Requirements
- Automated SSL certificate renewal
- Log rotation
- Dependency updates (via uv)
- Security patches
- Monitoring and alerting setup

## Success Metrics

### Launch Criteria
- [ ] All 5 tools implemented and tested
- [ ] HTTPS connection working with valid certificate
- [ ] Streaming HTTP functioning correctly
- [ ] nginx proxy configured correctly
- [ ] All external API integrations working
- [ ] Documentation complete
- [ ] Deployment automated

### Key Performance Indicators
- Tool response time (p95, p99)
- Error rate per tool
- SSL certificate renewal success rate
- Server uptime percentage
- Concurrent connection capacity

## Future Considerations

### Phase 2 Features (Out of Scope for v1.0)
- Authentication and authorization
- Additional tools (file operations, database queries, etc.)
- WebSocket support for bi-directional streaming
- Admin dashboard
- Usage analytics and metrics
- Load balancing for high availability
- Docker containerization
- Kubernetes deployment

### Potential Enhancements
- Caching layer for weather/search results
- Tool usage analytics
- Custom tool marketplace/plugin system
- Multi-region deployment
- GraphQL API in addition to MCP

## Risks and Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| External API rate limits | Medium | Medium | Implement caching, rate limiting, graceful degradation |
| SSL certificate renewal failure | High | Low | Monitoring alerts, manual renewal procedure documentation |
| DDoS attacks | High | Medium | Rate limiting, CDN (future), IP blocking |
| Breaking changes in MCP spec | Medium | Low | Pin MCP library versions, monitor spec changes |
| Python/dependency vulnerabilities | Medium | Medium | Regular updates, security scanning |

## Appendix

### References
- [Model Context Protocol Specification](https://modelcontextprotocol.io/)
- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- [uv Documentation](https://docs.astral.sh/uv/)
- [nginx Documentation](https://nginx.org/en/docs/)
- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)

### Glossary
- **MCP**: Model Context Protocol - a protocol for enabling AI assistants to interact with external tools
- **uv**: A fast Python package installer and resolver
- **FastMCP**: A Python framework for building MCP servers
- **nginx**: High-performance HTTP server and reverse proxy
- **Let's Encrypt**: Free, automated certificate authority for SSL/TLS certificates
- **Streaming HTTP**: HTTP connection that remains open for continuous data transmission

### Change Log
| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-11-12 | [Your Name] | Initial PRD creation |
