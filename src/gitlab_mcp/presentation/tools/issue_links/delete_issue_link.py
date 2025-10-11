"""Delete a link between two issues in GitLab."""

import asyncio
from typing import Any

from fastmcp import Context
from gitlab_mcp.presentation.tools.common.helpers import get_user_context
from gitlab_mcp.services.gitlab_client_factory import GitLabClientFactory

# Module-level instances (will be injected by server)
client_factory = GitLabClientFactory()


async def delete_issue_link(
    project_id: str,
    issue_iid: int,
    link_id: int,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Delete a link between two issues in GitLab.

    Args:
        project_id: Source project ID or path
        issue_iid: Source issue IID (internal ID)
        link_id: Issue link ID to delete
        ctx: FastMCP context for multi-tenant support

    Returns:
        Dictionary containing deletion status

    Example:
        >>> result = await delete_issue_link("my-project", 123, 789)
    """

    def _sync_delete_issue_link() -> dict[str, Any]:
        user_ctx = get_user_context(ctx)
        gl = client_factory.get_client(user_ctx)

        # Get the project and issue
        try:
            project = gl.projects.get(project_id)
            issue = project.issues.get(issue_iid)
        except Exception as e:
            raise ValueError(f"Issue '{project_id}#{issue_iid}' not found: {e}")

        # Get the issue link
        try:
            link = issue.links.get(link_id)
        except Exception as e:
            raise ValueError(f"Issue link '{link_id}' not found: {e}")

        # Delete the issue link
        try:
            link.delete()
        except Exception as e:
            raise ValueError(f"Failed to delete issue link: {e}")

        return {
            "success": True,
            "message": f"Issue link {link_id} deleted successfully",
            "deleted_link_id": link_id,
            "source_issue_iid": issue_iid,
        }

    return await asyncio.to_thread(_sync_delete_issue_link)
