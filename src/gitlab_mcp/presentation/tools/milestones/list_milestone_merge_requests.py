"""List milestone merge requests tool."""

import asyncio
from typing import Any

import gitlab
from fastmcp import Context
from gitlab_mcp.presentation.tools.common.helpers import get_user_context
from gitlab_mcp.services.gitlab_client_factory import GitLabClientFactory

# Module-level instances (will be injected by server)
client_factory = GitLabClientFactory()


async def list_milestone_merge_requests(
    project_id: str,
    milestone_id: int,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """List all merge requests in a milestone.

    Args:
        project_id: GitLab project ID or namespace/project path
        milestone_id: Milestone ID
        ctx: FastMCP context (auto-injected)

    Returns:
        List of merge requests in the milestone

    Raises:
        ValueError: If project or milestone not found
        gitlab.exceptions.GitlabGetError: If retrieval fails
    """

    def _sync_list_milestone_merge_requests() -> dict[str, Any]:
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

        # 5. Get merge requests in milestone
        merge_requests = milestone.merge_requests()

        # 6. Return serialized response
        return {
            "merge_requests": [
                {
                    "id": mr.id,
                    "iid": mr.iid,
                    "title": mr.title,
                    "state": mr.state,
                    "web_url": mr.web_url,
                }
                for mr in merge_requests
            ]
        }

    # Run sync code in thread pool (python-gitlab is sync, FastMCP is async)
    return await asyncio.to_thread(_sync_list_milestone_merge_requests)
