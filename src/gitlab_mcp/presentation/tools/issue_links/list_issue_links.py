"""List all links for a GitLab issue."""

import asyncio
from typing import Any

from fastmcp import Context
from gitlab_mcp.presentation.tools.common.helpers import get_user_context
from gitlab_mcp.services.gitlab_client_factory import GitLabClientFactory

# Module-level instances (will be injected by server)
client_factory = GitLabClientFactory()


async def list_issue_links(
    project_id: str,
    issue_iid: int,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """List all links for a GitLab issue.

     Issue links represent relationships between issues (e.g., "relates to", "blocks").

    Args:
        project_id: Project ID or path (e.g., "gitlab-org/gitlab" or "123")
        issue_iid: Issue IID (internal ID)
        ctx: FastMCP context for multi-tenant support

    Returns:
        Dictionary containing:
        - links: List of issue link objects
        - total_results: Total number of links returned

    Example:
        >>> result = await list_issue_links("my-project", 42)
    """

    def _sync_list_issue_links() -> dict[str, Any]:
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

        # Get links
        links_list = issue.links.list()

        # Serialize links
        links = []
        for link in links_list:
            link_data = {
                "id": link.id,
                "iid": link.iid,
                "title": getattr(link, "title", None),
                "state": getattr(link, "state", None),
                "project_id": getattr(link, "project_id", None),
                "web_url": getattr(link, "web_url", None),
                "link_type": getattr(link, "link_type", "relates_to"),
            }
            links.append(link_data)

        return {
            "links": links,
            "total_results": len(links),
        }

    return await asyncio.to_thread(_sync_list_issue_links)
