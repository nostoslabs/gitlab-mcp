"""Delete a milestone from a GitLab project."""

import asyncio
from typing import Any

from fastmcp import Context
from gitlab_mcp.presentation.tools.common.helpers import get_user_context
from gitlab_mcp.services.gitlab_client_factory import GitLabClientFactory

# Module-level instances (will be injected by server)
client_factory = GitLabClientFactory()


async def delete_milestone(
    project_id: str,
    milestone_id: int,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Delete a milestone from a GitLab project.

    Args:
        project_id: Project ID or path
        milestone_id: Milestone ID to delete
        ctx: FastMCP context for multi-tenant support

    Returns:
        Dictionary containing deletion status

    Example:
        >>> result = await delete_milestone("my-project", 123)
    """

    def _sync_delete_milestone() -> dict[str, Any]:
        user_ctx = get_user_context(ctx)
        gl = client_factory.get_client(user_ctx)

        # Get the project
        try:
            project = gl.projects.get(project_id)
        except Exception as e:
            raise ValueError(f"Project '{project_id}' not found: {e}")

        # Get the milestone
        try:
            milestone = project.milestones.get(milestone_id)
        except Exception as e:
            raise ValueError(f"Milestone '{milestone_id}' not found: {e}")

        # Store milestone info before deletion
        milestone_title = getattr(milestone, "title", None)

        # Delete the milestone
        try:
            milestone.delete()
        except Exception as e:
            raise ValueError(f"Failed to delete milestone: {e}")

        return {
            "success": True,
            "message": f"Milestone '{milestone_title}' (ID: {milestone_id}) deleted successfully",
            "deleted_milestone_id": milestone_id,
            "deleted_milestone_title": milestone_title,
        }

    return await asyncio.to_thread(_sync_delete_milestone)
