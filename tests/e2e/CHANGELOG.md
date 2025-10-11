# HTTP Streaming Test - Implementation Notes

## Transport Used: Streamable HTTP

The tests use FastMCP's **streamable-http** transport, which is the current standard for MCP over HTTP.

### Why Streamable HTTP?

- **SSE is deprecated**: The MCP standard is phasing out Server-Sent Events (SSE)
- **Streamable HTTP**: The current recommended transport for HTTP-based MCP servers
- **Bidirectional**: Supports full request/response cycles over HTTP
- **Standard**: Uses standard HTTP POST requests with JSON-RPC payloads

## Key Implementation Details

### Starting the Server

```python
from gitlab_mcp.server import mcp

# Use streamable-http transport (not 'sse' or 'http')
mcp.run(transport="streamable-http", host="127.0.0.1", port=8765)
```

### Sending Requests

The MCP protocol over HTTP uses JSON-RPC 2.0 format:

```python
import httpx

async with httpx.AsyncClient() as client:
    # Standard JSON-RPC request
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/list",
        "params": {}
    }

    # POST to /message endpoint
    response = await client.post(
        "http://127.0.0.1:8765/message",
        json=request,
        headers={"Content-Type": "application/json"}
    )

    # Parse JSON-RPC response
    result = response.json()
```

### Endpoint Structure

- **Base URL**: `http://host:port`
- **Message Endpoint**: `POST /message`
- **Content-Type**: `application/json`
- **Protocol**: JSON-RPC 2.0

## FastMCP Transport Options

FastMCP supports three transport modes:

1. **stdio** (default): For CLI tools and local integrations
2. **sse**: Legacy Server-Sent Events (deprecated)
3. **streamable-http**: Current HTTP streaming standard ✅

## Testing Coverage

The test suite validates:

1. ✅ Server starts with streamable-http transport
2. ✅ Tools can be listed via HTTP endpoint
3. ✅ Tools can be called via HTTP requests
4. ✅ Server information can be retrieved
5. ✅ Multiple concurrent requests are handled correctly
6. ✅ Responses follow MCP protocol format

## Running the Tests

```bash
# Set GitLab token
export GITLAB_PERSONAL_ACCESS_TOKEN="your-token"

# Run the HTTP streaming test
uv run pytest tests/e2e/test_http_streaming.py -v

# Run with verbose output
uv run pytest tests/e2e/test_http_streaming.py -vv

# Run directly (includes detailed console output)
uv run python tests/e2e/test_http_streaming.py
```

## Ports Used

- **8765**: Primary test server
- **8766**: Concurrent requests test

Ensure these ports are available before running tests.

## Architecture Benefits

### Streamable HTTP vs Stdio

**Streamable HTTP advantages:**
- Multiple concurrent clients
- Network-accessible (remote deployment)
- Standard HTTP tooling (curl, Postman, etc.)
- Load balancing and reverse proxy support
- Web service integration

**Stdio advantages:**
- Lower latency (no network overhead)
- Simpler local integration
- Process isolation
- CLI tool compatibility

## Future Enhancements

Potential additions to the test suite:

- [ ] Test with authentication headers
- [ ] Test with HTTPS/TLS
- [ ] Load testing with many concurrent clients
- [ ] WebSocket upgrade testing
- [ ] Error handling and retry logic
- [ ] Response streaming validation
- [ ] Connection pooling behavior
- [ ] Timeout handling

## References

- [MCP Specification](https://spec.modelcontextprotocol.io/)
- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- [JSON-RPC 2.0 Specification](https://www.jsonrpc.org/specification)
