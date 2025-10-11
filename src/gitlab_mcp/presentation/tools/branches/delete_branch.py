"""Delete branch tool."""

import asyncio
from typing import Any

import gitlab
from fastmcp import Context
from gitlab_mcp.presentation.tools.common.helpers import get_user_context
from gitlab_mcp.services.gitlab_client_factory import GitLabClientFactory

# Module-level instances (will be injected by server)
client_factory = GitLabClientFactory()


async def delete_branch(
    project_id: str,
    branch: str,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Delete a branch from a GitLab project.

    Args:
        project_id: GitLab project ID or namespace/project path
        branch: Name of the branch to delete
        ctx: FastMCP context (auto-injected)

    Returns:
        Success message with branch name

    Raises:
        ValueError: If project not found or branch deletion fails
        gitlab.exceptions.GitlabDeleteError: If deletion fails
    """

    def _sync_delete_branch() -> dict[str, Any]:
        # 1. Get user context (multi-tenant) or use default
        user_ctx = get_user_context(ctx)

        # 2. Get GitLab client for this user
        gl = client_factory.get_client(user_ctx)

        # 3. Get project using python-gitlab
        try:
            project = gl.projects.get(project_id)
        except gitlab.exceptions.GitlabGetError as e:
            raise ValueError(f"Project {project_id} not found") from e

        # 4. Delete branch
        try:
            project.branches.delete(branch)
        except gitlab.exceptions.GitlabDeleteError as e:
            raise ValueError(f"Failed to delete branch {branch}: {e}") from e

        # 5. Return success message
        return {
            "success": True,
            "branch": branch,
            "message": f"Branch '{branch}' deleted successfully",
        }

    # Run sync code in thread pool (python-gitlab is sync, FastMCP is async)
    return await asyncio.to_thread(_sync_delete_branch)
