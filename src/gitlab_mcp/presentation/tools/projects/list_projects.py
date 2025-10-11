"""List projects tool."""

import asyncio
from typing import Any

from fastmcp import Context
from gitlab_mcp.presentation.tools.common.helpers import get_user_context
from gitlab_mcp.services.gitlab_client_factory import GitLabClientFactory

# Module-level instances (will be injected by server)
client_factory = GitLabClientFactory()


async def list_projects(
    search: str | None = None,
    owned: bool = False,
    starred: bool = False,
    visibility: str | None = None,
    page: int = 1,
    per_page: int = 20,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """List GitLab projects.

    Args:
        search: Search query
        owned: Only owned projects
        starred: Only starred projects
        visibility: Filter by visibility ('public', 'internal', 'private')
        page: Page number
        per_page: Results per page
        ctx: FastMCP context

    Returns:
        List of projects with pagination info
    """

    def _sync_list() -> dict[str, Any]:
        # 1. Get user context
        user_ctx = get_user_context(ctx)

        # 2. Get GitLab client
        gl = client_factory.get_client(user_ctx)

        # 3. Build query parameters
        kwargs: dict[str, Any] = {"page": page, "per_page": per_page}
        if search:
            kwargs["search"] = search
        if owned:
            kwargs["owned"] = True
        if starred:
            kwargs["starred"] = True
        if visibility:
            kwargs["visibility"] = visibility

        # 4. Get projects
        projects = gl.projects.list(**kwargs)

        # 5. Return serialized response
        return {
            "projects": [
                {
                    "id": p.id,
                    "name": p.name,
                    "path": p.path,
                    "path_with_namespace": p.path_with_namespace,
                    "description": p.description,
                    "web_url": p.web_url,
                    "default_branch": getattr(p, "default_branch", None),
                }
                for p in projects
            ],
            "total": len(projects),
            "page": page,
            "per_page": per_page,
        }

    # Run sync code in thread pool (python-gitlab is sync, FastMCP is async)
    return await asyncio.to_thread(_sync_list)
