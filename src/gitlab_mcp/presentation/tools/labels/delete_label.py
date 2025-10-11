"""Delete a label from a GitLab project."""

import asyncio
from typing import Any

from fastmcp import Context
from gitlab_mcp.presentation.tools.common.helpers import get_user_context
from gitlab_mcp.services.gitlab_client_factory import GitLabClientFactory

# Module-level instances (will be injected by server)
client_factory = GitLabClientFactory()


async def delete_label(
    project_id: str,
    label_name: str,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Delete a label from a GitLab project.

    Args:
        project_id: Project ID or path
        label_name: Label name to delete
        ctx: FastMCP context for multi-tenant support

    Returns:
        Dictionary containing deletion status

    Example:
        >>> result = await delete_label("my-project", "old-label")
    """

    def _sync_delete_label() -> dict[str, Any]:
        user_ctx = get_user_context(ctx)
        gl = client_factory.get_client(user_ctx)

        # Get the project
        try:
            project = gl.projects.get(project_id)
        except Exception as e:
            raise ValueError(f"Project '{project_id}' not found: {e}")

        # Get the label
        try:
            label = project.labels.get(label_name)
        except Exception as e:
            raise ValueError(f"Label '{label_name}' not found: {e}")

        # Delete the label
        try:
            label.delete()
        except Exception as e:
            raise ValueError(f"Failed to delete label: {e}")

        return {
            "success": True,
            "message": f"Label '{label_name}' deleted successfully",
            "deleted_label": label_name,
        }

    return await asyncio.to_thread(_sync_delete_label)
