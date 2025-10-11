"""List merge requests tool."""

import asyncio
from typing import Any

import gitlab
from fastmcp import Context
from gitlab_mcp.presentation.tools.common.helpers import get_user_context
from gitlab_mcp.services.gitlab_client_factory import GitLabClientFactory

# Module-level instances (will be injected by server)
client_factory = GitLabClientFactory()


async def list_merge_requests(
    project_id: str,
    state: str | None = None,
    labels: list[str] | None = None,
    search: str | None = None,
    page: int = 1,
    per_page: int = 20,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """List merge requests in a project.

    Args:
        project_id: GitLab project ID or path
        state: Filter by state ('opened', 'closed', 'merged', 'all')
        labels: Filter by labels
        search: Search in title and description
        page: Page number (1-indexed)
        per_page: Results per page (max 100)
        ctx: FastMCP context

    Returns:
        List of merge requests with pagination info

    Raises:
        ValueError: If project not found
    """

    def _sync_list() -> dict[str, Any]:
        # 1. Get user context
        user_ctx = get_user_context(ctx)

        # 2. Get GitLab client
        gl = client_factory.get_client(user_ctx)

        # 3. Get project
        try:
            project = gl.projects.get(project_id)
        except gitlab.exceptions.GitlabGetError as e:
            raise ValueError(f"Project '{project_id}' not found") from e

        # 4. Build query parameters
        kwargs: dict[str, Any] = {"page": page, "per_page": per_page}
        if state:
            kwargs["state"] = state
        if labels:
            kwargs["labels"] = ",".join(labels)
        if search:
            kwargs["search"] = search

        # 5. Get merge requests with pagination
        merge_requests = project.mergerequests.list(**kwargs)

        # 6. Return serialized response
        return {
            "merge_requests": [
                {
                    "id": mr.id,
                    "iid": mr.iid,
                    "title": mr.title,
                    "state": mr.state,
                    "labels": mr.labels,
                    "web_url": mr.web_url,
                    "source_branch": mr.source_branch,
                    "target_branch": mr.target_branch,
                }
                for mr in merge_requests
            ],
            "total": len(merge_requests),
            "page": page,
            "per_page": per_page,
        }

    # Run sync code in thread pool (python-gitlab is sync, FastMCP is async)
    return await asyncio.to_thread(_sync_list)
