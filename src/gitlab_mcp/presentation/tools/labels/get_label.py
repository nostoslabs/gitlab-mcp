"""Get details of a specific label in a GitLab project."""

import asyncio
from typing import Any

from fastmcp import Context
from gitlab_mcp.presentation.tools.common.helpers import get_user_context
from gitlab_mcp.services.gitlab_client_factory import GitLabClientFactory

# Module-level instances (will be injected by server)
client_factory = GitLabClientFactory()


async def get_label(
    project_id: str,
    label_id: int,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Get details of a specific label in a GitLab project.

    Args:
        project_id: Project ID or path (e.g., "gitlab-org/gitlab" or "123")
        label_id: Label ID
        ctx: FastMCP context for multi-tenant support

    Returns:
        Dictionary containing label details:
        - id: Label ID
        - name: Label name
        - color: Label color (hex code)
        - description: Label description
        - open_issues_count: Number of open issues with this label
        - closed_issues_count: Number of closed issues with this label
        - open_merge_requests_count: Number of open merge requests with this label

    Example:
        >>> result = await get_label("my-project", 123)
    """

    def _sync_get_label() -> dict[str, Any]:
        user_ctx = get_user_context(ctx)
        gl = client_factory.get_client(user_ctx)

        # Get the project
        try:
            project = gl.projects.get(project_id)
        except Exception as e:
            raise ValueError(f"Project '{project_id}' not found: {e}")

        # Get the label
        try:
            label = project.labels.get(label_id)
        except Exception as e:
            raise ValueError(f"Label '{label_id}' not found: {e}")

        # Serialize label
        return {
            "id": label.id,
            "name": label.name,
            "color": label.color,
            "description": getattr(label, "description", None),
            "open_issues_count": getattr(label, "open_issues_count", 0),
            "closed_issues_count": getattr(label, "closed_issues_count", 0),
            "open_merge_requests_count": getattr(label, "open_merge_requests_count", 0),
        }

    return await asyncio.to_thread(_sync_get_label)
