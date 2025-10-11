"""List labels in a GitLab project."""

import asyncio
from typing import Any

from fastmcp import Context
from gitlab_mcp.presentation.tools.common.helpers import get_user_context
from gitlab_mcp.services.gitlab_client_factory import GitLabClientFactory

# Module-level instances (will be injected by server)
client_factory = GitLabClientFactory()


async def list_labels(
    project_id: str,
    search: str | None = None,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """List all labels in a GitLab project.

    Args:
        project_id: Project ID or path (e.g., "gitlab-org/gitlab" or "123")
        search: Optional search string to filter labels by name
        ctx: FastMCP context for multi-tenant support

    Returns:
        Dictionary containing:
        - labels: List of label objects with id, name, color, description, counts
        - total_results: Total number of labels returned

    Example:
        >>> result = await list_labels("my-project")
        >>> result = await list_labels("my-project", search="bug")
    """

    def _sync_list_labels() -> dict[str, Any]:
        user_ctx = get_user_context(ctx)
        gl = client_factory.get_client(user_ctx)

        # Get the project
        try:
            project = gl.projects.get(project_id)
        except Exception as e:
            raise ValueError(f"Project '{project_id}' not found: {e}")

        # Build filter parameters
        kwargs: dict[str, Any] = {}
        if search:
            kwargs["search"] = search

        # Get labels
        labels_list = project.labels.list(**kwargs)

        # Serialize labels
        labels = []
        for label in labels_list:
            label_data = {
                "id": label.id,
                "name": label.name,
                "color": label.color,
                "description": getattr(label, "description", None),
                "open_issues_count": getattr(label, "open_issues_count", 0),
                "closed_issues_count": getattr(label, "closed_issues_count", 0),
                "open_merge_requests_count": getattr(label, "open_merge_requests_count", 0),
            }
            labels.append(label_data)

        return {
            "labels": labels,
            "total_results": len(labels),
        }

    return await asyncio.to_thread(_sync_list_labels)
