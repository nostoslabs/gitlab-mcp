# Transport Comparison: Stdio vs Streamable HTTP

## Overview

This document compares the two main transport modes for the GitLab MCP server:
- **Stdio**: Process-based communication (default)
- **Streamable HTTP**: Network-based communication

## Starting the Server

### Stdio Mode (Default)
```python
from gitlab_mcp.server import mcp

# Run with stdio transport (default)
mcp.run()
# or explicitly:
mcp.run(transport="stdio")
```

### Streamable HTTP Mode
```python
from gitlab_mcp.server import mcp

# Run with streamable HTTP transport
mcp.run(transport="streamable-http", host="127.0.0.1", port=8765)
```

## Client Communication

### Stdio Mode
```python
import subprocess
import json

# Start server as subprocess
process = subprocess.Popen(
    ["python", "-m", "gitlab_mcp"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
)

# Send JSON-RPC request via stdin
request = {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}
process.stdin.write(json.dumps(request).encode() + b"\n")
process.stdin.flush()

# Read response from stdout
response = process.stdout.readline()
result = json.loads(response)
```

### Streamable HTTP Mode
```python
import httpx
import json

# Send JSON-RPC request via HTTP POST
async with httpx.AsyncClient() as client:
    request = {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}
    response = await client.post(
        "http://127.0.0.1:8765/message",
        json=request,
        headers={"Content-Type": "application/json"}
    )
    result = response.json()
```

## Test Patterns

### Stdio Test Pattern
```python
@pytest.mark.asyncio
async def test_with_stdio():
    """Test using stdio transport."""
    from gitlab_mcp.presentation.tools.projects.list_projects import list_projects

    # Call tool function directly
    result = await list_projects(per_page=5)

    # Validate result
    assert "projects" in result
    assert len(result["projects"]) <= 5
```

### Streamable HTTP Test Pattern
```python
@pytest.mark.asyncio
async def test_with_streamable_http():
    """Test using streamable HTTP transport."""
    # 1. Start server in background
    server_thread = run_server_in_thread(host="127.0.0.1", port=8765)
    wait_for_server("http://127.0.0.1:8765")

    # 2. Send MCP request via HTTP
    async with httpx.AsyncClient() as client:
        mcp_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "gitlab_list_projects",
                "arguments": {"per_page": 5}
            }
        }
        response = await client.post(
            "http://127.0.0.1:8765/message",
            json=mcp_request
        )

    # 3. Parse MCP response
    response_data = response.json()
    result = response_data["result"]

    # Extract tool result from content
    tool_result = json.loads(result["content"][0]["text"])
    assert "projects" in tool_result
```

## Key Differences

| Feature | Stdio | Streamable HTTP |
|---------|-------|-----------------|
| **Use Case** | Local CLI tools, scripts | Web services, remote access |
| **Connection** | Process pipes (stdin/stdout) | TCP socket (HTTP) |
| **Concurrency** | Single request at a time | Multiple concurrent requests |
| **Deployment** | Local machine | Any network location |
| **Testing** | Direct function calls or subprocess | HTTP client (httpx, curl, etc.) |
| **Debugging** | Process stdout/stderr | HTTP logs, browser DevTools |
| **Scalability** | Single process | Multiple clients, load balancing |
| **Latency** | Very low (IPC) | Network latency |
| **Security** | Process isolation | HTTP(S), authentication |

## When to Use Each

### Use Stdio When:
- Building command-line tools
- Integrating with local development environments (IDEs, editors)
- Maximum performance needed (no network overhead)
- Running on the same machine as the client
- Simple single-user scenarios

### Use Streamable HTTP When:
- Deploying as a web service
- Multiple clients need to connect
- Remote access is required
- Integration with web applications
- Need to scale horizontally
- Want to use standard HTTP tooling (reverse proxies, load balancers)

## Protocol Comparison

Both modes use the same JSON-RPC protocol, just over different transports:

### JSON-RPC Request (Same for Both)
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "gitlab_list_projects",
    "arguments": {
      "per_page": 5
    }
  }
}
```

### JSON-RPC Response (Same for Both)
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "{\"projects\": [...], \"total_results\": 42}"
      }
    ]
  }
}
```

## Running Tests

### Run Stdio Tests (Unit/Validation)
```bash
# Unit tests call tools directly
uv run pytest tests/unit/ -v

# Validation tests call tools directly
uv run pytest tests/validation/ -v
```

### Run Streamable HTTP Tests (E2E)
```bash
# E2E tests use streamable HTTP transport
export GITLAB_PERSONAL_ACCESS_TOKEN="your-token"
uv run pytest tests/e2e/test_http_streaming.py -v
```

## Performance Considerations

### Stdio
- **Latency**: ~0.1-1ms (IPC overhead)
- **Throughput**: Limited by single process
- **Memory**: Minimal (shared process memory)

### Streamable HTTP
- **Latency**: ~1-10ms (network + HTTP overhead)
- **Throughput**: Scales with concurrent connections
- **Memory**: Per-connection overhead

## Example: Running Both Modes

### Terminal 1: Start Streamable HTTP Server
```bash
# Start server with streamable HTTP transport
python -c "from gitlab_mcp.server import mcp; mcp.run(transport='streamable-http', host='127.0.0.1', port=8765)"
```

### Terminal 2: Test with curl
```bash
# Send JSON-RPC request
curl -X POST http://127.0.0.1:8765/message \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/list",
    "params": {}
  }'
```

### Terminal 3: Start Stdio Server
```bash
# Start server with stdio transport (default)
python -m gitlab_mcp

# Or through MCP client (e.g., Claude Desktop)
# Configure in MCP settings with command: python -m gitlab_mcp
```
