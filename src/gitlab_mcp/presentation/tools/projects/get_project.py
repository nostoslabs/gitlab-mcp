"""Get project tool."""

import asyncio
from typing import Any

import gitlab
from fastmcp import Context
from gitlab_mcp.presentation.tools.common.helpers import get_user_context
from gitlab_mcp.services.gitlab_client_factory import GitLabClientFactory

# Module-level instances (will be injected by server)
client_factory = GitLabClientFactory()


async def get_project(
    project_id: str,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Get a specific project by ID or path.

    Args:
        project_id: GitLab project ID or namespace/project path
        ctx: FastMCP context (auto-injected)

    Returns:
        Project details including id, name, path, description, etc.

    Raises:
        ValueError: If project not found
        gitlab.exceptions.GitlabGetError: If retrieval fails
    """

    def _sync_get() -> dict[str, Any]:
        # 1. Get user context
        user_ctx = get_user_context(ctx)

        # 2. Get GitLab client for this user
        gl = client_factory.get_client(user_ctx)

        # 3. Get project
        try:
            project = gl.projects.get(project_id)
        except gitlab.exceptions.GitlabGetError as e:
            raise ValueError(f"Project {project_id} not found") from e

        # 4. Return serialized response
        return {
            "id": project.id,
            "name": project.name,
            "path": project.path,
            "path_with_namespace": project.path_with_namespace,
            "description": project.description,
            "web_url": project.web_url,
            "default_branch": getattr(project, "default_branch", None),
            "visibility": project.visibility,
            "created_at": project.created_at,
            "last_activity_at": project.last_activity_at,
        }

    # Run sync code in thread pool
    return await asyncio.to_thread(_sync_get)
