"""Create a link between two issues in GitLab."""

import asyncio
from typing import Any

from fastmcp import Context
from gitlab_mcp.presentation.tools.common.helpers import get_user_context
from gitlab_mcp.services.gitlab_client_factory import GitLabClientFactory

# Module-level instances (will be injected by server)
client_factory = GitLabClientFactory()


async def create_issue_link(
    project_id: str,
    issue_iid: int,
    target_project_id: str,
    target_issue_iid: int,
    link_type: str = "relates_to",
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Create a link between two issues in GitLab.

    Args:
        project_id: Source project ID or path
        issue_iid: Source issue IID (internal ID)
        target_project_id: Target project ID or path
        target_issue_iid: Target issue IID
        link_type: Type of link ('relates_to', 'blocks', 'is_blocked_by')
        ctx: FastMCP context for multi-tenant support

    Returns:
        Dictionary containing created issue link details

    Example:
        >>> result = await create_issue_link("my-project", 123, "other-project", 456, "relates_to")
    """

    def _sync_create_issue_link() -> dict[str, Any]:
        user_ctx = get_user_context(ctx)
        gl = client_factory.get_client(user_ctx)

        # Get the source project and issue
        try:
            project = gl.projects.get(project_id)
            issue = project.issues.get(issue_iid)
        except Exception as e:
            raise ValueError(f"Source issue '{project_id}#{issue_iid}' not found: {e}")

        # Get the target project
        try:
            target_project = gl.projects.get(target_project_id)
        except Exception as e:
            raise ValueError(f"Target project '{target_project_id}' not found: {e}")

        # Create the issue link
        try:
            link_data = {
                "target_project_id": target_project.id,
                "target_issue_iid": target_issue_iid,
            }
            if link_type and link_type != "relates_to":
                link_data["link_type"] = link_type

            link = issue.links.create(link_data)
        except Exception as e:
            raise ValueError(f"Failed to create issue link: {e}")

        # Serialize issue link
        return {
            "id": link.id,
            "source_issue": {
                "iid": issue.iid,
                "project_id": project.id,
                "title": getattr(issue, "title", None),
            },
            "target_issue": {
                "iid": target_issue_iid,
                "project_id": target_project.id,
            },
            "link_type": getattr(link, "link_type", "relates_to"),
            "created_at": getattr(link, "created_at", None),
        }

    return await asyncio.to_thread(_sync_create_issue_link)
