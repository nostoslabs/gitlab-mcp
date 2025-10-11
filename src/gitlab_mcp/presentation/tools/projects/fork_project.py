"""Fork a GitLab project."""

import asyncio
from typing import Any

from fastmcp import Context
from gitlab_mcp.presentation.tools.common.helpers import get_user_context
from gitlab_mcp.services.gitlab_client_factory import GitLabClientFactory

# Module-level instances (will be injected by server)
client_factory = GitLabClientFactory()


async def fork_project(
    project_id: str,
    namespace_id: int | None = None,
    name: str | None = None,
    path: str | None = None,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Fork a GitLab project to your account or specified namespace.

    Args:
        project_id: Source project ID or path to fork
        namespace_id: Target namespace ID (group or user) for the fork
        name: Name for the forked project (defaults to original name)
        path: Path for the forked project (defaults to original path)
        ctx: FastMCP context for multi-tenant support

    Returns:
        Dictionary containing forked project details

    Example:
        >>> result = await fork_project("gitlab-org/gitlab")
    """

    def _sync_fork_project() -> dict[str, Any]:
        user_ctx = get_user_context(ctx)
        gl = client_factory.get_client(user_ctx)

        # Get the source project
        try:
            project = gl.projects.get(project_id)
        except Exception as e:
            raise ValueError(f"Project '{project_id}' not found: {e}")

        # Build fork parameters
        fork_params: dict[str, Any] = {}
        if namespace_id:
            fork_params["namespace_id"] = namespace_id
        if name:
            fork_params["name"] = name
        if path:
            fork_params["path"] = path

        # Fork the project
        try:
            forked_project = project.forks.create(fork_params)
        except Exception as e:
            raise ValueError(f"Failed to fork project: {e}")

        # Serialize forked project
        return {
            "id": forked_project.id,
            "name": forked_project.name,
            "path": forked_project.path,
            "path_with_namespace": getattr(forked_project, "path_with_namespace", None),
            "description": getattr(forked_project, "description", None),
            "web_url": getattr(forked_project, "web_url", None),
            "forked_from_project": {
                "id": project.id,
                "path_with_namespace": getattr(project, "path_with_namespace", None),
            },
        }

    return await asyncio.to_thread(_sync_fork_project)
