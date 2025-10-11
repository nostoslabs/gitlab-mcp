"""Get milestone burndown tool."""

import asyncio
from typing import Any

import gitlab
from fastmcp import Context
from gitlab_mcp.presentation.tools.common.helpers import get_user_context
from gitlab_mcp.services.gitlab_client_factory import GitLabClientFactory

# Module-level instances (will be injected by server)
client_factory = GitLabClientFactory()


async def get_milestone_burndown(
    project_id: str,
    milestone_id: int,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Get milestone burndown chart data and statistics.

    Args:
        project_id: GitLab project ID or namespace/project path
        milestone_id: Milestone ID
        ctx: FastMCP context (auto-injected)

    Returns:
        Milestone burndown data and statistics

    Raises:
        ValueError: If project or milestone not found
        gitlab.exceptions.GitlabGetError: If retrieval fails
    """

    def _sync_get_milestone_burndown() -> dict[str, Any]:
        # 1. Get user context (multi-tenant) or use default
        user_ctx = get_user_context(ctx)

        # 2. Get GitLab client for this user
        gl = client_factory.get_client(user_ctx)

        # 3. Get project using python-gitlab
        try:
            project = gl.projects.get(project_id)
        except gitlab.exceptions.GitlabGetError as e:
            raise ValueError(f"Project {project_id} not found") from e

        # 4. Get milestone with full data (lazy=False loads all attributes)
        try:
            milestone = project.milestones.get(milestone_id, lazy=False)
        except gitlab.exceptions.GitlabGetError as e:
            raise ValueError(f"Milestone {milestone_id} not found") from e

        # 5. Extract statistics from milestone attributes
        # GitLab API includes issue counts in milestone data
        attrs = milestone.attributes if hasattr(milestone, "attributes") else {}

        statistics = {
            "total_issues_count": attrs.get("total_issues_count", 0),
            "closed_issues_count": attrs.get("closed_issues_count", 0),
        }

        # Calculate open issues count
        total = statistics["total_issues_count"]
        closed = statistics["closed_issues_count"]
        statistics["open_issues_count"] = total - closed

        # 6. Return serialized response
        return {
            "milestone_id": milestone.id,
            "title": milestone.title,
            "state": milestone.state,
            "due_date": milestone.due_date if hasattr(milestone, "due_date") else None,
            "start_date": milestone.start_date if hasattr(milestone, "start_date") else None,
            "statistics": statistics,
        }

    # Run sync code in thread pool (python-gitlab is sync, FastMCP is async)
    return await asyncio.to_thread(_sync_get_milestone_burndown)
