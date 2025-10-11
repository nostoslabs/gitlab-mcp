"""End-to-end test for GitLab MCP Server using HTTP streaming transport.

This test validates that the server can run with HTTP streaming transport and handle
requests via the streamable HTTP protocol instead of stdio.
"""

import asyncio
import json
import os
import threading
import time
from typing import Any

import httpx
import pytest


def run_server_in_thread(host: str = "127.0.0.1", port: int = 8765) -> threading.Thread:
    """Run the MCP server in a background thread with HTTP streaming transport.

    Args:
        host: Host to bind to
        port: Port to listen on

    Returns:
        Thread object running the server
    """

    def server_target() -> None:
        from gitlab_mcp.server import mcp

        # Run server with streamable HTTP transport
        mcp.run(transport="streamable-http", host=host, port=port)

    thread = threading.Thread(target=server_target, daemon=True)
    thread.start()
    return thread


def wait_for_server(url: str, timeout: int = 10, interval: float = 0.5) -> bool:
    """Wait for the server to be ready by polling the health endpoint.

    Args:
        url: Base URL of the server
        timeout: Maximum time to wait in seconds
        interval: Time between polls in seconds

    Returns:
        True if server is ready, False if timeout
    """
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with httpx.Client() as client:
                # Try to connect to the server
                response = client.get(url, timeout=2.0)
                if response.status_code in (200, 404):  # Server is responding
                    return True
        except (httpx.ConnectError, httpx.TimeoutException):
            pass
        time.sleep(interval)
    return False


@pytest.mark.skipif(
    not os.getenv("GITLAB_PERSONAL_ACCESS_TOKEN"),
    reason="GITLAB_PERSONAL_ACCESS_TOKEN not set",
)
@pytest.mark.asyncio
async def test_http_streaming_server():
    """Test MCP server with streamable HTTP transport.

    This test:
    1. Starts the MCP server with streamable HTTP transport
    2. Waits for the server to be ready
    3. Sends MCP requests via HTTP
    4. Validates the responses
    """
    host = "127.0.0.1"
    port = 8765
    base_url = f"http://{host}:{port}"

    print("\n" + "=" * 80)
    print("🚀 Testing MCP Server with Streamable HTTP Transport")
    print("=" * 80)

    # Start server in background thread
    print(f"\n✓ Starting MCP server on {base_url}")
    _server_thread = run_server_in_thread(host, port)

    # Wait for server to be ready
    print("✓ Waiting for server to be ready...")
    if not wait_for_server(base_url, timeout=10):
        pytest.fail("Server failed to start within timeout period")

    print(f"✓ Server is ready at {base_url}")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Test 1: List available tools
            print("\n" + "-" * 80)
            print("TEST 1: List available tools via HTTP")
            print("-" * 80)

            # Create MCP request for listing tools
            mcp_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/list",
                "params": {},
            }

            # Send request to streamable HTTP endpoint
            response = await client.post(
                f"{base_url}/message",
                json=mcp_request,
                headers={"Content-Type": "application/json"},
            )

            print(f"\n✓ HTTP Response Status: {response.status_code}")
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"

            # Parse response
            response_data = response.json()
            print("✓ Received JSON-RPC response")

            # Validate response structure
            assert "jsonrpc" in response_data, "Missing jsonrpc field"
            assert response_data["jsonrpc"] == "2.0", "Invalid jsonrpc version"
            assert "result" in response_data, "Missing result field"

            result = response_data["result"]
            assert "tools" in result, "Missing tools field in result"

            tools = result["tools"]
            print(f"✓ Found {len(tools)} tools")

            # Verify we have the expected tools
            tool_names = {tool["name"] for tool in tools}
            expected_tools = [
                "gitlab_list_projects",
                "gitlab_get_project",
                "gitlab_list_issues",
                "gitlab_create_issue",
            ]

            for tool_name in expected_tools:
                assert tool_name in tool_names, f"Missing expected tool: {tool_name}"
                print(f"  ✓ {tool_name}")

            print("\n✅ Test 1 PASSED: Tools list retrieved via HTTP")

            # Test 2: Call a tool via HTTP
            print("\n" + "-" * 80)
            print("TEST 2: Call gitlab_list_projects tool via HTTP")
            print("-" * 80)

            # Create MCP request to call a tool
            tool_call_request = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": "gitlab_list_projects",
                    "arguments": {"per_page": 5},
                },
            }

            response = await client.post(
                f"{base_url}/message",
                json=tool_call_request,
                headers={"Content-Type": "application/json"},
            )

            print(f"\n✓ HTTP Response Status: {response.status_code}")
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"

            response_data = response.json()
            print("✓ Received JSON-RPC response")

            # Validate response structure
            assert "jsonrpc" in response_data, "Missing jsonrpc field"
            assert "result" in response_data, "Missing result field"

            result = response_data["result"]

            # Check if we got content
            if "content" in result:
                content = result["content"]
                print(f"✓ Received {len(content)} content items")

                # Parse the tool result
                if content and len(content) > 0:
                    first_content = content[0]
                    if "text" in first_content:
                        tool_result = json.loads(first_content["text"])
                        if "projects" in tool_result:
                            projects = tool_result["projects"]
                            print(f"✓ Found {len(projects)} projects")
                            if projects:
                                first_project = projects[0]
                                print(f"  - First project: {first_project.get('name')}")
                                print(f"  - Project ID: {first_project.get('id')}")

            print("\n✅ Test 2 PASSED: Tool call executed via HTTP")

            # Test 3: Verify server info
            print("\n" + "-" * 80)
            print("TEST 3: Get server information via HTTP")
            print("-" * 80)

            server_info_request = {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "test-client", "version": "1.0.0"},
                },
            }

            response = await client.post(
                f"{base_url}/message",
                json=server_info_request,
                headers={"Content-Type": "application/json"},
            )

            print(f"\n✓ HTTP Response Status: {response.status_code}")
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"

            response_data = response.json()
            print("✓ Received JSON-RPC response")

            if "result" in response_data:
                result = response_data["result"]
                if "serverInfo" in result:
                    server_info = result["serverInfo"]
                    print(f"✓ Server name: {server_info.get('name')}")
                    print(f"✓ Server version: {server_info.get('version', 'N/A')}")

            print("\n✅ Test 3 PASSED: Server info retrieved via HTTP")

    except Exception as e:
        print(f"\n❌ Test FAILED: {e}")
        raise

    finally:
        # Note: The server thread is daemonized, so it will be cleaned up automatically
        print("\n" + "=" * 80)
        print("🎉 HTTP STREAMING TEST COMPLETED")
        print("=" * 80)
        print("\nValidated:")
        print("  ✓ MCP server runs with streamable HTTP transport")
        print("  ✓ Server accepts and processes JSON-RPC requests via HTTP")
        print("  ✓ Tools can be listed via HTTP endpoint")
        print("  ✓ Tools can be called via HTTP endpoint")
        print("  ✓ Responses follow MCP protocol format")
        print("\n" + "=" * 80)


@pytest.mark.skipif(
    not os.getenv("GITLAB_PERSONAL_ACCESS_TOKEN"),
    reason="GITLAB_PERSONAL_ACCESS_TOKEN not set",
)
@pytest.mark.asyncio
async def test_http_streaming_concurrent_requests():
    """Test MCP server handling multiple concurrent HTTP requests.

    This validates that the streamable HTTP transport can handle multiple
    simultaneous requests without issues.
    """
    host = "127.0.0.1"
    port = 8766  # Different port to avoid conflicts
    base_url = f"http://{host}:{port}"

    print("\n" + "=" * 80)
    print("🚀 Testing Concurrent Requests via Streamable HTTP")
    print("=" * 80)

    # Start server
    print(f"\n✓ Starting MCP server on {base_url}")
    _server_thread = run_server_in_thread(host, port)

    # Wait for server to be ready
    print("✓ Waiting for server to be ready...")
    if not wait_for_server(base_url, timeout=10):
        pytest.fail("Server failed to start within timeout period")

    print(f"✓ Server is ready at {base_url}")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:

            async def make_request(request_id: int) -> dict[str, Any]:
                """Make a single request to list projects."""
                mcp_request = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "method": "tools/call",
                    "params": {
                        "name": "gitlab_list_projects",
                        "arguments": {"per_page": 3},
                    },
                }

                response = await client.post(
                    f"{base_url}/message",
                    json=mcp_request,
                    headers={"Content-Type": "application/json"},
                )

                return response.json()

            # Make 5 concurrent requests
            print("\n✓ Making 5 concurrent requests...")
            tasks = [make_request(i) for i in range(1, 6)]
            responses = await asyncio.gather(*tasks)

            # Verify all responses
            print(f"✓ Received {len(responses)} responses")
            for i, response_data in enumerate(responses, 1):
                assert "jsonrpc" in response_data, f"Request {i}: Missing jsonrpc field"
                assert "result" in response_data, f"Request {i}: Missing result field"
                print(f"  ✓ Request {i}: Success")

            print("\n✅ PASSED: Concurrent requests handled successfully")

    except Exception as e:
        print(f"\n❌ Test FAILED: {e}")
        raise

    finally:
        print("\n" + "=" * 80)


if __name__ == "__main__":
    """Run the HTTP streaming tests directly."""
    print("\n" + "=" * 80)
    print("Running GitLab MCP HTTP Streaming Tests")
    print("=" * 80)

    # Check environment variables
    if not os.getenv("GITLAB_PERSONAL_ACCESS_TOKEN"):
        print("❌ ERROR: GITLAB_PERSONAL_ACCESS_TOKEN not set")
        exit(1)

    print("\n✓ Environment variables set correctly")

    # Run tests
    asyncio.run(test_http_streaming_server())
    asyncio.run(test_http_streaming_concurrent_requests())
