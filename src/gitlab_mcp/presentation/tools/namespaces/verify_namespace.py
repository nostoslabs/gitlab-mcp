"""Verify namespace availability in GitLab."""

import asyncio
from typing import Any

from fastmcp import Context
from gitlab_mcp.presentation.tools.common.helpers import get_user_context
from gitlab_mcp.services.gitlab_client_factory import GitLabClientFactory

# Module-level instances (will be injected by server)
client_factory = GitLabClientFactory()


async def verify_namespace(
    namespace_path: str,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Verify if a namespace path is available or already taken.

    This is useful when creating new groups or checking if a namespace exists.

    Args:
        namespace_path: Namespace path to check (e.g., "my-group")
        ctx: FastMCP context for multi-tenant support

    Returns:
        Dictionary containing:
        - path: The namespace path that was checked
        - available: Whether the namespace is available (True/False)
        - exists: Whether the namespace exists (True/False)
        - namespace: Namespace details if it exists, None otherwise

    Example:
        >>> result = await verify_namespace("my-group")
        >>> if result["available"]:
        ...     print("Namespace is available!")
    """

    def _sync_verify_namespace() -> dict[str, Any]:
        user_ctx = get_user_context(ctx)
        gl = client_factory.get_client(user_ctx)

        # Try to find namespace by path
        try:
            # Search for namespaces with the exact path
            namespaces = gl.namespaces.list(search=namespace_path)

            # Check if any namespace has an exact path match
            matching_namespace = None
            for ns in namespaces:
                if ns.path == namespace_path:
                    matching_namespace = ns
                    break

            if matching_namespace:
                return {
                    "path": namespace_path,
                    "available": False,
                    "exists": True,
                    "namespace": {
                        "id": matching_namespace.id,
                        "name": matching_namespace.name,
                        "path": matching_namespace.path,
                        "kind": getattr(matching_namespace, "kind", None),
                        "full_path": getattr(matching_namespace, "full_path", None),
                    },
                }
            else:
                return {
                    "path": namespace_path,
                    "available": True,
                    "exists": False,
                    "namespace": None,
                }
        except Exception as e:
            # If search fails, assume namespace doesn't exist
            return {
                "path": namespace_path,
                "available": True,
                "exists": False,
                "namespace": None,
                "error": str(e),
            }

    return await asyncio.to_thread(_sync_verify_namespace)
