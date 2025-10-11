"""Update an existing label in a GitLab project."""

import asyncio
from typing import Any

from fastmcp import Context
from gitlab_mcp.presentation.tools.common.helpers import get_user_context
from gitlab_mcp.services.gitlab_client_factory import GitLabClientFactory

# Module-level instances (will be injected by server)
client_factory = GitLabClientFactory()


async def update_label(
    project_id: str,
    label_name: str,
    new_name: str | None = None,
    color: str | None = None,
    description: str | None = None,
    priority: int | None = None,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Update an existing label in a GitLab project.

    Args:
        project_id: Project ID or path
        label_name: Current label name (required for identification)
        new_name: New label name (optional)
        color: New label color in hex format (e.g., '#FF0000')
        description: New label description
        priority: New label priority (integer)
        ctx: FastMCP context for multi-tenant support

    Returns:
        Dictionary containing updated label details

    Example:
          >>> result = await update_label("my-project", "bug", color="#00FF00")
    """

    def _sync_update_label() -> dict[str, Any]:
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

        # Build update data
        update_data: dict[str, Any] = {}

        if new_name:
            update_data["new_name"] = new_name
        if color:
            update_data["color"] = color
        if description is not None:
            update_data["description"] = description
        if priority is not None:
            update_data["priority"] = priority

        # Update the label
        try:
            for key, value in update_data.items():
                setattr(label, key, value)
            label.save()
        except Exception as e:
            raise ValueError(f"Failed to update label: {e}")

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

    return await asyncio.to_thread(_sync_update_label)
