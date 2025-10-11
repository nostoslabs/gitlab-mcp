"""Get details of a specific namespace in GitLab."""

import asyncio
from typing import Any

from fastmcp import Context
from gitlab_mcp.presentation.tools.common.helpers import get_user_context
from gitlab_mcp.services.gitlab_client_factory import GitLabClientFactory

# Module-level instances (will be injected by server)
client_factory = GitLabClientFactory()


async def get_namespace(
    namespace_id: int,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Get details of a specific namespace in GitLab.

    Args:
        namespace_id: Namespace ID
        ctx: FastMCP context for multi-tenant support

    Returns:
        Dictionary containing namespace details:
        - id: Namespace ID
        - name: Namespace name
        - path: Namespace path (URL slug)
        - kind: Namespace kind (user or group)
        - full_path: Full path including parent namespaces
        - parent_id: Parent namespace ID (if nested)
        - avatar_url: Namespace avatar URL
        - web_url: Web URL to the namespace

    Example:
        >>> result = await get_namespace(123)
    """

    def _sync_get_namespace() -> dict[str, Any]:
        user_ctx = get_user_context(ctx)
        gl = client_factory.get_client(user_ctx)

        # Get the namespace
        try:
            namespace = gl.namespaces.get(namespace_id)
        except Exception as e:
            raise ValueError(f"Namespace '{namespace_id}' not found: {e}")

        # Serialize namespace
        return {
            "id": namespace.id,
            "name": namespace.name,
            "path": namespace.path,
            "kind": getattr(namespace, "kind", None),
            "full_path": getattr(namespace, "full_path", None),
            "parent_id": getattr(namespace, "parent_id", None),
            "avatar_url": getattr(namespace, "avatar_url", None),
            "web_url": getattr(namespace, "web_url", None),
            "description": getattr(namespace, "description", None),
        }

    return await asyncio.to_thread(_sync_get_namespace)
