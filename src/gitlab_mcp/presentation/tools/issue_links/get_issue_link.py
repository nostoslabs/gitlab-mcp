"""Get details of a specific issue link."""

import asyncio
from typing import Any

from fastmcp import Context
from gitlab_mcp.presentation.tools.common.helpers import get_user_context
from gitlab_mcp.services.gitlab_client_factory import GitLabClientFactory

# Module-level instances (will be injected by server)
client_factory = GitLabClientFactory()


async def get_issue_link(
    project_id: str,
    issue_iid: int,
    link_id: int,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Get details of a specific issue link.

    Args:
        project_id: Project ID or path (e.g., "gitlab-org/gitlab" or "123")
        issue_iid: Issue IID (internal ID)
        link_id: Link ID
        ctx: FastMCP context for multi-tenant support

    Returns:
        Dictionary containing the issue link:
        - id: Link ID
        - iid: Issue IID
        - title: Issue title
        - state: Issue state
        - project_id: Project ID
        - web_url: Web URL to the issue
        - link_type: Type of link (relates_to, blocks, is_blocked_by)

    Example:
        >>> result = await get_issue_link("my-project", 42, 123)
    """

    def _sync_get_issue_link() -> dict[str, Any]:
        user_ctx = get_user_context(ctx)
        gl = client_factory.get_client(user_ctx)

        # Get the project
        try:
            project = gl.projects.get(project_id)
        except Exception as e:
            raise ValueError(f"Project '{project_id}' not found: {e}")

        # Get the issue
        try:
            issue = project.issues.get(issue_iid)
        except Exception as e:
            raise ValueError(f"Issue '{issue_iid}' not found: {e}")

        # Get the link
        try:
            link = issue.links.get(link_id)
        except Exception as e:
            raise ValueError(f"Link '{link_id}' not found: {e}")

        # Serialize link
        return {
            "id": link.id,
            "iid": link.iid,
            "title": getattr(link, "title", None),
            "state": getattr(link, "state", None),
            "project_id": getattr(link, "project_id", None),
            "web_url": getattr(link, "web_url", None),
            "link_type": getattr(link, "link_type", "relates_to"),
        }

    return await asyncio.to_thread(_sync_get_issue_link)
