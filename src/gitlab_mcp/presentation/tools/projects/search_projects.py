"""Search projects tool."""

import asyncio
from typing import Any

from fastmcp import Context
from gitlab_mcp.presentation.tools.common.helpers import get_user_context
from gitlab_mcp.services.gitlab_client_factory import GitLabClientFactory

# Module-level instances (will be injected by server)
client_factory = GitLabClientFactory()


async def search_projects(
    search: str,
    page: int = 1,
    per_page: int = 20,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Search GitLab projects.

    Args:
        search: Search query (required)
        page: Page number
        per_page: Results per page
        ctx: FastMCP context

    Returns:
        List of matching projects with pagination info

    Raises:
        ValueError: If search query is empty
    """
    if not search:
        raise ValueError("Search query is required")

    def _sync_search() -> dict[str, Any]:
        # 1. Get user context
        user_ctx = get_user_context(ctx)

        # 2. Get GitLab client
        gl = client_factory.get_client(user_ctx)

        # 3. Search projects using python-gitlab
        projects = gl.projects.list(search=search, page=page, per_page=per_page)

        # 4. Return serialized response
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
    return await asyncio.to_thread(_sync_search)
