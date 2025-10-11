"""Create a new GitLab project."""

import asyncio
from typing import Any

from fastmcp import Context
from gitlab_mcp.presentation.tools.common.helpers import get_user_context
from gitlab_mcp.services.gitlab_client_factory import GitLabClientFactory

# Module-level instances (will be injected by server)
client_factory = GitLabClientFactory()


async def create_project(
    name: str,
    description: str | None = None,
    visibility: str = "private",
    initialize_with_readme: bool = False,
    namespace_id: int | None = None,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Create a new GitLab project.

    Args:
        name: Project name (required)
        description: Project description
        visibility: Project visibility ('private', 'internal', 'public')
        initialize_with_readme: Initialize project with README file
        namespace_id: Namespace ID (group or user namespace) to create project in
        ctx: FastMCP context for multi-tenant support

    Returns:
        Dictionary containing created project details

    Example:
        >>> result = await create_project("my-new-project", description="Test project")
    """

    def _sync_create_project() -> dict[str, Any]:
        user_ctx = get_user_context(ctx)
        gl = client_factory.get_client(user_ctx)

        # Build project data
        project_data: dict[str, Any] = {
            "name": name,
            "visibility": visibility,
        }

        if description:
            project_data["description"] = description
        if initialize_with_readme:
            project_data["initialize_with_readme"] = True
        if namespace_id:
            project_data["namespace_id"] = namespace_id

        # Create the project
        try:
            project = gl.projects.create(project_data)
        except Exception as e:
            raise ValueError(f"Failed to create project: {e}")

        # Serialize project
        return {
            "id": project.id,
            "name": project.name,
            "path": project.path,
            "path_with_namespace": getattr(project, "path_with_namespace", None),
            "description": getattr(project, "description", None),
            "visibility": getattr(project, "visibility", None),
            "web_url": getattr(project, "web_url", None),
            "created_at": getattr(project, "created_at", None),
            "default_branch": getattr(project, "default_branch", None),
        }

    return await asyncio.to_thread(_sync_create_project)
