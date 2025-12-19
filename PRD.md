# Product Requirements Document: MCP Test Server

## 1\. Executive Summary

The **MCP Test Server** is a specialized HTTP server designed to host Model Context Protocol (MCP) tools. Its primary purpose is to assist with offensive security testing of MCP clients. The server supports streamable HTTP responses, multiple authentication modes, and dynamic tool registration via a web interface. It is designed to be container-native for easy deployment on platforms like Heroku.

## 2\. Technical Architecture

### 2.1 Technology Stack

  * **Language:** Python (FastAPI)
  * **Package Management** uv with virtual environments
  * **Protocol:** MCP over Streamable HTTP (as per 2025-03-26 spec). JSON-RPC 2.0.
  * **Containerization:** Docker (Dockerfile required).
  * **Deployment Target:** Heroku / Cloud Container Services.

### 2.2 System Context

The server acts as a remote host. MCP Clients (e.g., AI Agents, IDEs) connect to this server to discover and execute tools.


## 3\. Functional Requirements

### 3.1 Core Server Capabilities

  * **FR-01:** The application MUST run as an HTTP server.
  * **FR-02:** The server MUST implement the **Streamable HTTP** transport as defined in the MCP specification (2025-03-26).
      * It MUST provide a single endpoint (e.g. `/mcp`) for JSON-RPC messages.
      * It MUST NOT use the deprecated HTTP+SSE (connect-then-post) transport.
      * It MUST support HTTP POST for incoming JSON-RPC messages.
      * It MUST support `text/event-stream` responses for streaming results or server-initiated requests.
  * **FR-03:** The server MUST support the `tools/list` JSON-RPC method for Tool Discovery.
  * **FR-04:** The server MUST support the `tools/call` JSON-RPC method for Tool Execution.

### 3.2 Default Toolset

The server must boot with the following tools available by default:

#### Tool A: Echo

  * **Name:** `echo`
  * **Description:** Repeats the input back to the caller.
  * **Parameters:**
      * `saythis` (string, required): The text to repeat.
  * **Logic:** Return the value of `saythis`.

#### Tool B: IP Inspector

  * **Name:** `source_ip`
  * **Description:** Returns the apparent source IP address of the requester.
  * **Parameters:** None.
  * **Logic:** Extract the IP from the HTTP Request headers (e.g., `X-Forwarded-For` or `Remote-Addr`).

#### Tool C: Weather

  * **Name:** `weather`
  * **Description:** Returns current weather for a location.
  * **Parameters:**
      * `postal_code` (string, required): The zip/postal code.
  * **Logic:** Fetch weather data from the Open Weather Map API (https://openweathermap.org/api)

### 3.3 Dynamic Tool Registration

  * **FR-05:** The server MUST serve a static HTML frontend at the root URL (`/` or `/admin`).
  * **FR-06:** The frontend MUST contain a form with fields:
      * Tool Name
      * Tool Description
      * Parameter Name (Single string parameter support is sufficient for MVP)
  * **FR-07:** Submitting the form MUST send a POST request to the backend to register the new tool in memory. Additionally, the server itself must be updated to add the new tool such that it persists across restarts.
  * **FR-08:** The new tool MUST immediately be visible in the Tool Discovery endpoint.

### 3.4 Authentication

The security layer is controlled by the `AUTH_MODE` environment variable.

#### Mode 1: No Authentication

  * **Config:** `AUTH_MODE=none` (Default)
  * **Behavior:** All endpoints accept requests without validation.

#### Mode 2: OAuth 2.1

  * **Config:** `AUTH_MODE=oauth2`
  * **Behavior:**
      * Protect endpoints.
      * Implement standard OAuth 2.1 flows (e.g., Client Credentials or Authorization Code).
      * Reject requests without a valid Bearer token.

#### Mode 3: Simple Token

  * **Config:** `AUTH_MODE=token`
  * **Behavior:**
      * Server expects a static token (defined via `AUTH_TOKEN` env var or generated on startup).
      * Validate `Authorization: Bearer <token>` header.
      * Return `401 Unauthorized` if the token is missing or invalid.

## 4\. Non-Functional Requirements

  * **NFR-01 (Deployment):** The repository MUST include a `Dockerfile` optimized for production (multi-stage build preferred).
  * **NFR-02 (Configuration):** All configuration (ports, auth modes, keys) MUST be handled via Environment Variables.
  * **NFR-03 (Logging):** The server MUST log incoming requests, specifically noting the source IP and the tool being requested (to support the "Offensive Security" auditing aspect).

## 5\. API Interface Specification (Draft)

### 5.1 Endpoints

| Method | Path | Description | Auth Required? |
| :--- | :--- | :--- | :--- |
| `POST` | `/mcp` | Main MCP JSON-RPC endpoint. | Yes (if enabled) |
| `GET` | `/mcp` | (Optional) SSE listening endpoint. | Yes (if enabled) |
| `GET` | `/` | Web UI for adding tools. | No |
| `POST` | `/admin/add-tool` | API to register a new tool from the UI. | No (for MVP) |

### 5.2 Environment Variables

```bash
PORT=8080               # Port to listen on
AUTH_MODE=none          # Options: none, oauth2, token
AUTH_TOKEN=secret123    # Required if AUTH_MODE=token
OAUTH_CLIENT_ID=...     # Required if AUTH_MODE=oauth2
OAUTH_CLIENT_SECRET=... # Required if AUTH_MODE=oauth2
```

## 6\. Development Phases

1.  **Setup:** Initialize Git, Dockerfile, and basic HTTP server skeleton.
2.  **Core Logic:** Implement the MCP Protocol handling (Discovery/Execution).
3.  **Default Tools:** Implement Echo, IP, and Weather logic.
4.  **Dynamic UI:** Build the HTML form and the registration backend logic.
5.  **Security:** Implement the Middleware to handle `AUTH_MODE` switching.
6.  **Testing:** Verify Docker build and Heroku compatibility.
