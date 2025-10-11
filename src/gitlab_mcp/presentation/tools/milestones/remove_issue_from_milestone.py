"""Remove issue from milestone tool."""

import asyncio
from typing import Any

import gitlab
from fastmcp import Context
from gitlab_mcp.presentation.tools.common.helpers import get_user_context
from gitlab_mcp.services.gitlab_client_factory import GitLabClientFactory

# Module-level instances (will be injected by server)
client_factory = GitLabClientFactory()


async def remove_issue_from_milestone(
    project_id: str,
    issue_iid: int,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Remove an issue from its milestone.

    Args:
        project_id: GitLab project ID or namespace/project path
        issue_iid: Issue IID (internal ID)
        ctx: FastMCP context (auto-injected)

    Returns:
        Success message with issue info

    Raises:
        ValueError: If project or issue not found
        gitlab.exceptions.GitlabUpdateError: If removal fails
    """

    def _sync_remove_issue_from_milestone() -> dict[str, Any]:
        # 1. Get user context (multi-tenant) or use default
        user_ctx = get_user_context(ctx)

        # 2. Get GitLab client for this user
        gl = client_factory.get_client(user_ctx)

        # 3. Get project using python-gitlab
        try:
            project = gl.projects.get(project_id)
        except gitlab.exceptions.GitlabGetError as e:
            raise ValueError(f"Project {project_id} not found") from e

        # 4. Get issue
        try:
            issue = project.issues.get(issue_iid)
        except gitlab.exceptions.GitlabGetError as e:
            raise ValueError(f"Issue {issue_iid} not found") from e

        # 5. Remove issue from milestone (set milestone_id to None)
        issue.milestone_id = None
        issue.save()

        # 6. Return serialized response
        return {
            "issue_iid": issue.iid,
            "message": f"Issue #{issue.iid} removed from milestone",
        }

    # Run sync code in thread pool (python-gitlab is sync, FastMCP is async)
    return await asyncio.to_thread(_sync_remove_issue_from_milestone)
