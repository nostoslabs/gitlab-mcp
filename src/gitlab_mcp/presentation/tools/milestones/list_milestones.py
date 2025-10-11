"""List milestones tool."""

import asyncio
from typing import Any

import gitlab
from fastmcp import Context
from gitlab_mcp.presentation.tools.common.helpers import get_user_context
from gitlab_mcp.services.gitlab_client_factory import GitLabClientFactory

# Module-level instances (will be injected by server)
client_factory = GitLabClientFactory()


async def list_milestones(
    project_id: str,
    state: str | None = None,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """List all milestones in a GitLab project.

    Args:
        project_id: GitLab project ID or namespace/project path
        state: Optional milestone state to filter by (active, closed)
        ctx: FastMCP context (auto-injected)

    Returns:
        List of milestones with their details

    Raises:
        ValueError: If project not found
        gitlab.exceptions.GitlabListError: If listing fails
    """

    def _sync_list_milestones() -> dict[str, Any]:
        # 1. Get user context (multi-tenant) or use default
        user_ctx = get_user_context(ctx)

        # 2. Get GitLab client for this user
        gl = client_factory.get_client(user_ctx)

        # 3. Get project using python-gitlab
        try:
            project = gl.projects.get(project_id)
        except gitlab.exceptions.GitlabGetError as e:
            raise ValueError(f"Project {project_id} not found") from e

        # 4. List milestones with optional filters
        list_kwargs: dict[str, Any] = {"all": True}
        if state:
            list_kwargs["state"] = state

        milestones = project.milestones.list(**list_kwargs)

        # 5. Return serialized response
        return {
            "milestones": [
                {
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
                for milestone in milestones
            ]
        }

    # Run sync code in thread pool (python-gitlab is sync, FastMCP is async)
    return await asyncio.to_thread(_sync_list_milestones)
