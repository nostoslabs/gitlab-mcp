"""Delete issue tool."""

import asyncio
from typing import Any

import gitlab
from fastmcp import Context
from gitlab_mcp.presentation.tools.common.helpers import get_user_context
from gitlab_mcp.services.gitlab_client_factory import GitLabClientFactory

# Module-level instances (will be injected by server)
client_factory = GitLabClientFactory()


async def delete_issue(
    project_id: str,
    issue_iid: int,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Delete an issue from a GitLab project.

    Args:
        project_id: GitLab project ID or namespace/project path
        issue_iid: Issue IID (project-scoped ID) to delete
        ctx: FastMCP context (auto-injected)

    Returns:
        Success status and message

    Raises:
        ValueError: If project or issue not found
        gitlab.exceptions.GitlabDeleteError: If deletion fails
    """

    def _sync_delete() -> dict[str, Any]:
        # 1. Get user context
        user_ctx = get_user_context(ctx)

        # 2. Get GitLab client for this user
        gl = client_factory.get_client(user_ctx)

        # 3. Get project
        try:
            project = gl.projects.get(project_id)
        except gitlab.exceptions.GitlabGetError as e:
            raise ValueError(f"Project {project_id} not found") from e

        # 4. Get issue
        try:
            issue = project.issues.get(issue_iid)
        except gitlab.exceptions.GitlabGetError as e:
            raise ValueError(f"Issue {issue_iid} not found in project {project_id}") from e

        # 5. Delete issue
        issue.delete()

        # 6. Return success response
        return {
            "success": True,
            "message": f"Issue {issue_iid} deleted successfully",
        }

    # Run sync code in thread pool
    return await asyncio.to_thread(_sync_delete)
