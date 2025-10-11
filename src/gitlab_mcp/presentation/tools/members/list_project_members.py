"""List members of a GitLab project with their access levels."""

import asyncio
from typing import Any

from fastmcp import Context
from gitlab_mcp.presentation.tools.common.helpers import get_user_context
from gitlab_mcp.services.gitlab_client_factory import GitLabClientFactory

# Module-level instances (will be injected by server)
client_factory = GitLabClientFactory()


async def list_project_members(
    project_id: str,
    page: int = 1,
    per_page: int = 20,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """List members of a GitLab project with their access levels.

    Access levels:
    - 10: Guest
    - 20: Reporter
    - 30: Developer
    - 40: Maintainer
    - 50: Owner

    Args:
        project_id: Project ID or path (e.g., "gitlab-org/gitlab" or "123")
        page: Page number for pagination (default: 1)
        per_page: Number of members per page (default: 20, max: 100)
        ctx: FastMCP context for multi-tenant support

    Returns:
        Dictionary containing:
        - members: List of member objects with user details and access levels
        - total_results: Total number of members returned

    Example:
        >>> result = await list_project_members("my-project")
        >>> result = await list_project_members("my-project", page=2, per_page=50)
    """

    def _sync_list_project_members() -> dict[str, Any]:
        user_ctx = get_user_context(ctx)
        gl = client_factory.get_client(user_ctx)

        # Get the project
        try:
            project = gl.projects.get(project_id)
        except Exception as e:
            raise ValueError(f"Project '{project_id}' not found: {e}")

        # Get members
        members_list = project.members.list(page=page, per_page=per_page)

        # Serialize members
        members = []
        for member in members_list:
            member_data = {
                "id": member.id,
                "username": member.username,
                "name": member.name,
                "email": getattr(member, "email", None),
                "state": getattr(member, "state", None),
                "avatar_url": getattr(member, "avatar_url", None),
                "web_url": getattr(member, "web_url", None),
                "access_level": member.access_level,
                "expires_at": getattr(member, "expires_at", None),
            }
            members.append(member_data)

        return {
            "members": members,
            "total_results": len(members),
        }

    return await asyncio.to_thread(_sync_list_project_members)
