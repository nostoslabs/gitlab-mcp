"""List available namespaces in GitLab."""

import asyncio
from typing import Any

from fastmcp import Context
from gitlab_mcp.presentation.tools.common.helpers import get_user_context
from gitlab_mcp.services.gitlab_client_factory import GitLabClientFactory

# Module-level instances (will be injected by server)
client_factory = GitLabClientFactory()


async def list_namespaces(
    search: str | None = None,
    page: int = 1,
    per_page: int = 20,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """List available namespaces in GitLab.

    Namespaces include user namespaces and group namespaces.
    They are used as the first part of project paths (e.g., "username/project" or "group/project").

    Args:
        search: Optional search string to filter namespaces by name or path
        page: Page number for pagination (default: 1)
        per_page: Number of namespaces per page (default: 20, max: 100)
        ctx: FastMCP context for multi-tenant support

    Returns:
        Dictionary containing:
        - namespaces: List of namespace objects with id, name, path, kind
        - total_results: Total number of namespaces returned

    Example:
        >>> result = await list_namespaces()
        >>> result = await list_namespaces(search="gitlab")
    """

    def _sync_list_namespaces() -> dict[str, Any]:
        user_ctx = get_user_context(ctx)
        gl = client_factory.get_client(user_ctx)

        # Build filter parameters
        kwargs: dict[str, Any] = {
            "page": page,
            "per_page": per_page,
        }

        if search:
            kwargs["search"] = search

        # Get namespaces
        namespaces_list = gl.namespaces.list(**kwargs)

        # Serialize namespaces
        namespaces = []
        for namespace in namespaces_list:
            namespace_data = {
                "id": namespace.id,
                "name": namespace.name,
                "path": namespace.path,
                "kind": getattr(namespace, "kind", None),
                "full_path": getattr(namespace, "full_path", None),
                "parent_id": getattr(namespace, "parent_id", None),
                "avatar_url": getattr(namespace, "avatar_url", None),
                "web_url": getattr(namespace, "web_url", None),
            }
            namespaces.append(namespace_data)

        return {
            "namespaces": namespaces,
            "total_results": len(namespaces),
        }

    return await asyncio.to_thread(_sync_list_namespaces)
