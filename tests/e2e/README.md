# End-to-End Tests

This directory contains end-to-end tests that validate the GitLab MCP server with different transport protocols.

## HTTP Streaming Test

The `test_http_streaming.py` file tests the MCP server using streamable HTTP transport instead of stdio.

### What It Tests

1. **Server Startup**: Verifies the server can start with HTTP transport
2. **Tools Discovery**: Lists all available tools via HTTP endpoint
3. **Tool Execution**: Calls tools via HTTP and validates responses
4. **Server Information**: Retrieves server metadata via the initialize method
5. **Concurrent Requests**: Tests handling multiple simultaneous HTTP requests

### Running the Test

```bash
# Set up environment
export GITLAB_PERSONAL_ACCESS_TOKEN="your-token-here"

# Run the HTTP streaming test
uv run pytest tests/e2e/test_http_streaming.py -v

# Or run it directly
uv run python tests/e2e/test_http_streaming.py
```

### Test Architecture

The test:
- Starts the FastMCP server in a background thread with streamable HTTP transport
- Uses `httpx` to send JSON-RPC requests to the server
- Validates responses follow the MCP protocol specification
- Tests both single and concurrent requests

### Key Differences from Stdio Tests

| Aspect | Stdio | Streamable HTTP |
|--------|-------|-----------------|
| **Transport** | stdin/stdout pipes | HTTP POST requests |
| **Connection** | Process communication | Network socket |
| **Format** | JSON-RPC over stdio | JSON-RPC over HTTP |
| **Concurrency** | Sequential | Multiple simultaneous connections |
| **Deployment** | Local tools | Web services |

### Test Structure

```python
# 1. Start server in background thread with streamable HTTP
server_thread = run_server_in_thread(host="127.0.0.1", port=8765)

# 2. Wait for server to be ready
wait_for_server(base_url)

# 3. Send JSON-RPC request via HTTP
response = await client.post(
    f"{base_url}/message",
    json={"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}
)

# 4. Validate response
assert response.status_code == 200
assert response.json()["jsonrpc"] == "2.0"
```

### Ports Used

- **8765**: Primary HTTP streaming test
- **8766**: Concurrent requests test (to avoid port conflicts)

### Troubleshooting

**Server not starting:**
- Check if ports 8765/8766 are available
- Verify GITLAB_PERSONAL_ACCESS_TOKEN is set
- Check server logs for errors

**Connection timeouts:**
- Increase timeout in `wait_for_server()` function
- Check firewall settings
- Verify httpx can connect to localhost

**Test failures:**
- Ensure GitLab API token has necessary permissions
- Check network connectivity to gitlab.com
- Verify all dependencies are installed: `uv sync`
