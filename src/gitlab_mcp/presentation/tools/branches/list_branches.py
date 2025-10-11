"""List branches tool."""

import asyncio
from typing import Any

import gitlab
from fastmcp import Context
from gitlab_mcp.presentation.tools.common.helpers import get_user_context
from gitlab_mcp.services.gitlab_client_factory import GitLabClientFactory

# Module-level instances (will be injected by server)
client_factory = GitLabClientFactory()


async def list_branches(
    project_id: str,
    search: str | None = None,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """List all branches in a GitLab project.

    Args:
        project_id: GitLab project ID or namespace/project path
        search: Optional search string to filter branches
        ctx: FastMCP context (auto-injected)

    Returns:
        List of branches with their details

    Raises:
        ValueError: If project not found
        gitlab.exceptions.GitlabListError: If listing fails
    """

    def _sync_list_branches() -> dict[str, Any]:
        # 1. Get user context (multi-tenant) or use default
        user_ctx = get_user_context(ctx)

        # 2. Get GitLab client for this user
        gl = client_factory.get_client(user_ctx)

        # 3. Get project using python-gitlab
        try:
            project = gl.projects.get(project_id)
        except gitlab.exceptions.GitlabGetError as e:
            raise ValueError(f"Project {project_id} not found") from e

        # 4. List branches with optional search filter
        list_kwargs: dict[str, Any] = {"all": True}
        if search:
            list_kwargs["search"] = search

        branches = project.branches.list(**list_kwargs)

        # 5. Return serialized response
        return {
            "branches": [
                {
                    "name": branch.name,
                    "commit": branch.commit,
                    "merged": branch.merged,
                    "protected": branch.protected,
                    "developers_can_push": branch.developers_can_push,
                    "developers_can_merge": branch.developers_can_merge,
                    "can_push": branch.can_push,
                    "default": branch.default,
                    "web_url": branch.web_url,
                }
                for branch in branches
            ]
        }

    # Run sync code in thread pool (python-gitlab is sync, FastMCP is async)
    return await asyncio.to_thread(_sync_list_branches)
