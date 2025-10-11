"""Get milestone tool."""

import asyncio
from typing import Any

import gitlab
from fastmcp import Context
from gitlab_mcp.presentation.tools.common.helpers import get_user_context
from gitlab_mcp.services.gitlab_client_factory import GitLabClientFactory

# Module-level instances (will be injected by server)
client_factory = GitLabClientFactory()


async def get_milestone(
    project_id: str,
    milestone_id: int,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Get a specific milestone by ID.

    Args:
        project_id: GitLab project ID or namespace/project path
        milestone_id: Milestone ID
        ctx: FastMCP context (auto-injected)

    Returns:
        Milestone details

    Raises:
        ValueError: If project or milestone not found
        gitlab.exceptions.GitlabGetError: If retrieval fails
    """

    def _sync_get_milestone() -> dict[str, Any]:
        # 1. Get user context (multi-tenant) or use default
        user_ctx = get_user_context(ctx)

        # 2. Get GitLab client for this user
        gl = client_factory.get_client(user_ctx)

        # 3. Get project using python-gitlab
        try:
            project = gl.projects.get(project_id)
        except gitlab.exceptions.GitlabGetError as e:
            raise ValueError(f"Project {project_id} not found") from e

        # 4. Get milestone
        try:
            milestone = project.milestones.get(milestone_id)
        except gitlab.exceptions.GitlabGetError as e:
            raise ValueError(f"Milestone {milestone_id} not found") from e

        # 5. Return serialized response
        return {
            "id": milestone.id,
            "iid": milestone.iid,
            "title": milestone.title,
            "description": milestone.description,
            "state": milestone.state,
            "due_date": milestone.due_date,
            "start_date": milestone.start_date,
            "web_url": milestone.web_url,
            "created_at": milestone.created_at,
            "updated_at": milestone.updated_at,
        }

    # Run sync code in thread pool (python-gitlab is sync, FastMCP is async)
    return await asyncio.to_thread(_sync_get_milestone)
