"""Create a new label in a GitLab project."""

import asyncio
from typing import Any

from fastmcp import Context
from gitlab_mcp.presentation.tools.common.helpers import get_user_context
from gitlab_mcp.services.gitlab_client_factory import GitLabClientFactory

# Module-level instances (will be injected by server)
client_factory = GitLabClientFactory()


async def create_label(
    project_id: str,
    name: str,
    color: str,
    description: str | None = None,
    priority: int | None = None,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Create a new label in a GitLab project.

    Args:
        project_id: Project ID or path
        name: Label name (required)
        color: Label color in hex format (e.g., '#FF0000')
        description: Label description
        priority: Label priority (integer)
        ctx: FastMCP context for multi-tenant support

    Returns:
        Dictionary containing created label details

    Example:
        >>> result = await create_label("my-project", "bug", "#FF0000", "Bug tracking label")
    """

    def _sync_create_label() -> dict[str, Any]:
        user_ctx = get_user_context(ctx)
        gl = client_factory.get_client(user_ctx)

        # Get the project
        try:
            project = gl.projects.get(project_id)
        except Exception as e:
            raise ValueError(f"Project '{project_id}' not found: {e}")

        # Build label data
        label_data: dict[str, Any] = {
            "name": name,
            "color": color,
        }

        if description:
            label_data["description"] = description
        if priority is not None:
            label_data["priority"] = priority

        # Create the label
        try:
            label = project.labels.create(label_data)
        except Exception as e:
            raise ValueError(f"Failed to create label: {e}")

        # Serialize label
        return {
            "id": label.id,
            "name": label.name,
            "color": label.color,
            "description": getattr(label, "description", None),
            "priority": getattr(label, "priority", None),
            "open_issues_count": getattr(label, "open_issues_count", 0),
            "closed_issues_count": getattr(label, "closed_issues_count", 0),
            "open_merge_requests_count": getattr(label, "open_merge_requests_count", 0),
            "subscribed": getattr(label, "subscribed", False),
        }

    return await asyncio.to_thread(_sync_create_label)
