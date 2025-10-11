"""Create milestone tool."""

import asyncio
from typing import Any

import gitlab
from fastmcp import Context
from gitlab_mcp.presentation.tools.common.helpers import get_user_context
from gitlab_mcp.services.gitlab_client_factory import GitLabClientFactory

# Module-level instances (will be injected by server)
client_factory = GitLabClientFactory()


async def create_milestone(
    project_id: str,
    title: str,
    description: str | None = None,
    due_date: str | None = None,
    start_date: str | None = None,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Create a new milestone in a GitLab project.

    Args:
        project_id: GitLab project ID or namespace/project path
        title: Milestone title
        description: Optional milestone description
        due_date: Optional due date (YYYY-MM-DD format)
        start_date: Optional start date (YYYY-MM-DD format)
        ctx: FastMCP context (auto-injected)

    Returns:
        Created milestone details

    Raises:
        ValueError: If project not found
        gitlab.exceptions.GitlabCreateError: If creation fails
    """

    def _sync_create_milestone() -> dict[str, Any]:
        # 1. Get user context (multi-tenant) or use default
        user_ctx = get_user_context(ctx)

        # 2. Get GitLab client for this user
        gl = client_factory.get_client(user_ctx)

        # 3. Get project using python-gitlab
        try:
            project = gl.projects.get(project_id)
        except gitlab.exceptions.GitlabGetError as e:
            raise ValueError(f"Project {project_id} not found") from e

        # 4. Build milestone data
        milestone_data: dict[str, Any] = {
            "title": title,
        }
        if description is not None:
            milestone_data["description"] = description
        if due_date is not None:
            milestone_data["due_date"] = due_date
        if start_date is not None:
            milestone_data["start_date"] = start_date

        # 5. Create milestone
        milestone = project.milestones.create(milestone_data)

        # 6. Return serialized response
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
    return await asyncio.to_thread(_sync_create_milestone)
