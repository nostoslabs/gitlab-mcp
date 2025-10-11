"""Add issue to milestone tool."""

import asyncio
from typing import Any

import gitlab
from fastmcp import Context
from gitlab_mcp.presentation.tools.common.helpers import get_user_context
from gitlab_mcp.services.gitlab_client_factory import GitLabClientFactory

# Module-level instances (will be injected by server)
client_factory = GitLabClientFactory()


async def add_issue_to_milestone(
    project_id: str,
    issue_iid: int,
    milestone_id: int,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Assign an issue to a milestone.

    Args:
        project_id: GitLab project ID or namespace/project path
        issue_iid: Issue IID (internal ID)
        milestone_id: Milestone ID
        ctx: FastMCP context (auto-injected)

    Returns:
        Success message with issue and milestone info

    Raises:
        ValueError: If project, issue, or milestone not found
        gitlab.exceptions.GitlabUpdateError: If assignment fails
    """

    def _sync_add_issue_to_milestone() -> dict[str, Any]:
        # 1. Get user context (multi-tenant) or use default
        user_ctx = get_user_context(ctx)

        # 2. Get GitLab client for this user
        gl = client_factory.get_client(user_ctx)

        # 3. Get project using python-gitlab
        try:
            project = gl.projects.get(project_id)
        except gitlab.exceptions.GitlabGetError as e:
            raise ValueError(f"Project {project_id} not found") from e

        # 4. Get milestone (to verify it exists)
        try:
            milestone = project.milestones.get(milestone_id)
        except gitlab.exceptions.GitlabGetError as e:
            raise ValueError(f"Milestone {milestone_id} not found") from e

        # 5. Get issue
        try:
            issue = project.issues.get(issue_iid)
        except gitlab.exceptions.GitlabGetError as e:
            raise ValueError(f"Issue {issue_iid} not found") from e

        # 6. Assign issue to milestone
        issue.milestone_id = milestone_id
        issue.save()

        # 7. Return serialized response
        return {
            "issue_iid": issue.iid,
            "milestone_id": milestone.id,
            "milestone_title": milestone.title,
            "message": f"Issue #{issue.iid} added to milestone '{milestone.title}'",
        }

    # Run sync code in thread pool (python-gitlab is sync, FastMCP is async)
    return await asyncio.to_thread(_sync_add_issue_to_milestone)
