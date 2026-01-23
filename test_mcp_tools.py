import os
import sys
import json
import httpx
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
BASE_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8080")
if len(sys.argv) > 1:
    BASE_URL = sys.argv[1]
BASE_URL = BASE_URL.rstrip("/")  # Normalize URL to avoid double slashes

AUTH_MODE = os.getenv("AUTH_MODE", "none").lower()
AUTH_TOKEN = os.getenv("AUTH_TOKEN", "")
OAUTH_CLIENT_ID = os.getenv("OAUTH_CLIENT_ID", "")
OAUTH_CLIENT_SECRET = os.getenv("OAUTH_CLIENT_SECRET", "")

print(f"Target URL: {BASE_URL}")
print(f"Auth Mode: {AUTH_MODE}")

def get_auth_headers():
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream"
    }

    if AUTH_MODE == "none":
        return headers

    if AUTH_MODE == "token":
        if not AUTH_TOKEN:
            print("Error: AUTH_MODE is 'token' but AUTH_TOKEN is not set.")
            sys.exit(1)
        headers["Authorization"] = f"Bearer {AUTH_TOKEN}"
        return headers

    if AUTH_MODE == "oauth2":
        if not OAUTH_CLIENT_ID or not OAUTH_CLIENT_SECRET:
            print("Error: AUTH_MODE is 'oauth2' but OAUTH credentials are not set.")
            sys.exit(1)

        print("Getting OAuth2 token...")
        try:
            resp = httpx.post(
                f"{BASE_URL}/token",
                json={"client_id": OAUTH_CLIENT_ID, "client_secret": OAUTH_CLIENT_SECRET}
            )
            resp.raise_for_status()
            token_data = resp.json()
            access_token = token_data["access_token"]
            headers["Authorization"] = f"Bearer {access_token}"
            print("OAuth2 token obtained.")
            return headers
        except Exception as e:
            print(f"Failed to get OAuth token: {e}")
            sys.exit(1)

    return headers

def run_rpc(method: str, params: dict = None, req_id: int = 1):
    url = f"{BASE_URL}/mcp"
    headers = get_auth_headers()

    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "id": req_id
    }
    if params:
        payload["params"] = params

    try:
        print(f"\n--- Sending {method} ---")
        # print(f"Payload: {json.dumps(payload, indent=2)}")

        response = httpx.post(url, headers=headers, json=payload, timeout=10.0, follow_redirects=True)

        print(f"Status: {response.status_code}")
        if response.status_code == 307:
            print(f"Location: {response.headers.get('Location')}")
        if response.status_code == 200:
            data = None
            try:
                data = response.json()
            except json.JSONDecodeError:
                # Handle SSE response
                text = response.text
                for line in text.splitlines():
                    if line.startswith("data: "):
                        try:
                            data = json.loads(line[6:])
                            break
                        except:
                            pass

                if not data:
                    print("Response is not JSON or valid SSE:")
                    print(response.text)
                    return None

            print("Result:")
            print(json.dumps(data, indent=2))
            return data
        else:
            print("Error Response:")
            print(response.text)

    except Exception as e:
        print(f"Request failed: {e}")

def main():
    # 1. Initialize (optional but polite)
    run_rpc("initialize")

    # 2. List Tools
    list_resp = run_rpc("tools/list", req_id=2)

    if not list_resp or "result" not in list_resp:
        print("Failed to list tools. Aborting.")
        return

    tools = list_resp.get("result", {}).get("tools", [])
    print(f"\nFound {len(tools)} tools.")

    # 3. Call 'echo' tool
    print("\nTesting 'echo' tool...")
    run_rpc("tools/call", {
        "name": "echo",
        "arguments": {"saythis": "Hello MCP!"}
    }, req_id=3)

    # 4. Call 'sourceip' tool
    print("\nTesting 'sourceip' tool...")
    run_rpc("tools/call", {
        "name": "sourceip",
        "arguments": {}
    }, req_id=4)

    # 5. Call 'weather' tool
    print("\nTesting 'weather' tool...")
    run_rpc("tools/call", {
        "name": "weather",
        #"arguments": {"postal_code": "94105"} # San Francisco
        "arguments": {"postal_code": "90210"} # Beverly Hills
    }, req_id=5)

if __name__ == "__main__":
    main()

