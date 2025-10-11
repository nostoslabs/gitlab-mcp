"""Create branch tool."""

import asyncio
from typing import Any

import gitlab
from fastmcp import Context
from gitlab_mcp.presentation.tools.common.helpers import get_user_context
from gitlab_mcp.services.gitlab_client_factory import GitLabClientFactory

# Module-level instances (will be injected by server)
client_factory = GitLabClientFactory()


async def create_branch(
    project_id: str,
    branch: str,
    ref: str = "main",
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Create a new branch in a GitLab project.

    Args:
        project_id: GitLab project ID or namespace/project path
        branch: Name for the new branch
        ref: Source branch/commit for new branch (defaults to 'main')
        ctx: FastMCP context (auto-injected)

    Returns:
        Branch details including name, commit, protected status, etc.

    Raises:
        ValueError: If project not found or branch creation fails
        gitlab.exceptions.GitlabCreateError: If creation fails
    """

    def _sync_create_branch() -> dict[str, Any]:
        # 1. Get user context (multi-tenant) or use default
        user_ctx = get_user_context(ctx)

        # 2. Get GitLab client for this user
        gl = client_factory.get_client(user_ctx)

        # 3. Get project using python-gitlab
        try:
            project = gl.projects.get(project_id)
        except gitlab.exceptions.GitlabGetError as e:
            raise ValueError(f"Project {project_id} not found") from e

        # 4. Create branch
        try:
            branch_obj = project.branches.create({"branch": branch, "ref": ref})
        except gitlab.exceptions.GitlabCreateError as e:
            raise ValueError(f"Failed to create branch {branch}: {e}") from e

        # 5. Return serialized response
        return {
            "name": branch_obj.name,
            "commit": branch_obj.commit,
            "merged": branch_obj.merged,
            "protected": branch_obj.protected,
            "developers_can_push": branch_obj.developers_can_push,
            "developers_can_merge": branch_obj.developers_can_merge,
            "can_push": branch_obj.can_push,
            "default": branch_obj.default,
            "web_url": branch_obj.web_url,
        }

    # Run sync code in thread pool (python-gitlab is sync, FastMCP is async)
    return await asyncio.to_thread(_sync_create_branch)
