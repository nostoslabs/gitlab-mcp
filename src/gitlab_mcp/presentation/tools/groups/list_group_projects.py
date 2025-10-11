"""List projects in a GitLab group."""

import asyncio
from typing import Any

from fastmcp import Context
from gitlab_mcp.presentation.tools.common.helpers import get_user_context
from gitlab_mcp.services.gitlab_client_factory import GitLabClientFactory

# Module-level instances (will be injected by server)
client_factory = GitLabClientFactory()


async def list_group_projects(
    group_id: str,
    archived: bool = False,
    visibility: str | None = None,
    search: str | None = None,
    page: int = 1,
    per_page: int = 20,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """List all projects in a GitLab group.

    Args:
        group_id: Group ID or path (e.g., "gitlab-org" or "123")
        archived: Include archived projects (default: False)
        visibility: Filter by visibility ('public', 'internal', 'private')
        search: Search query to filter projects by name
        page: Page number for pagination (default: 1)
        per_page: Number of projects per page (default: 20, max: 100)
        ctx: FastMCP context for multi-tenant support

    Returns:
        Dictionary containing:
        - projects: List of project objects with id, name, path, description, etc.
        - total_results: Total number of projects returned

    Example:
        >>> result = await list_group_projects("gitlab-org")
        >>> result = await list_group_projects("my-group", visibility="public")
    """

    def _sync_list_group_projects() -> dict[str, Any]:
        user_ctx = get_user_context(ctx)
        gl = client_factory.get_client(user_ctx)

        # Get the group
        try:
            group = gl.groups.get(group_id)
        except Exception as e:
            raise ValueError(f"Group '{group_id}' not found: {e}")

        # Build filter parameters
        kwargs: dict[str, Any] = {
            "page": page,
            "per_page": per_page,
        }

        if archived:
            kwargs["archived"] = True
        if visibility:
            kwargs["visibility"] = visibility
        if search:
            kwargs["search"] = search

        # Get projects
        projects_list = group.projects.list(**kwargs)

        # Serialize projects
        projects = []
        for project in projects_list:
            project_data = {
                "id": project.id,
                "name": project.name,
                "path": project.path,
                "path_with_namespace": getattr(project, "path_with_namespace", None),
                "description": getattr(project, "description", None),
                "visibility": getattr(project, "visibility", None),
                "archived": getattr(project, "archived", False),
                "created_at": getattr(project, "created_at", None),
                "last_activity_at": getattr(project, "last_activity_at", None),
                "web_url": getattr(project, "web_url", None),
                "default_branch": getattr(project, "default_branch", None),
                "star_count": getattr(project, "star_count", 0),
                "forks_count": getattr(project, "forks_count", 0),
            }
            projects.append(project_data)

        return {
            "projects": projects,
            "total_results": len(projects),
        }

    return await asyncio.to_thread(_sync_list_group_projects)
