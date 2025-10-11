"""List issues tool."""

import asyncio
from typing import Any

import gitlab
from fastmcp import Context
from gitlab_mcp.presentation.tools.common.helpers import get_user_context
from gitlab_mcp.services.gitlab_client_factory import GitLabClientFactory

# Module-level instances (will be injected by server)
client_factory = GitLabClientFactory()


async def list_issues(
    project_id: str,
    state: str | None = None,
    labels: list[str] | None = None,
    search: str | None = None,
    page: int = 1,
    per_page: int = 20,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """List issues in a project.

    Args:
        project_id: GitLab project ID or namespace/project path
        state: Filter by state ('opened', 'closed', 'all')
        labels: Filter by labels
        search: Search in title and description
        page: Page number (1-indexed)
        per_page: Results per page (max 100)
        ctx: FastMCP context (auto-injected)

    Returns:
        Dictionary with 'issues' list and pagination info

    Raises:
        ValueError: If project not found
    """

    def _sync_list() -> dict[str, Any]:
        # 1. Get user context
        user_ctx = get_user_context(ctx)

        # 2. Get GitLab client for this user
        gl = client_factory.get_client(user_ctx)

        # 3. Get project
        try:
            project = gl.projects.get(project_id)
        except gitlab.exceptions.GitlabGetError as e:
            raise ValueError(f"Project {project_id} not found") from e

        # 4. Build query parameters
        kwargs: dict[str, Any] = {"page": page, "per_page": per_page}
        if state:
            kwargs["state"] = state
        if labels:
            kwargs["labels"] = ",".join(labels)
        if search:
            kwargs["search"] = search

        # 5. Get issues with pagination
        issues = project.issues.list(**kwargs)

        # 6. Return serialized response
        return {
            "issues": [
                {
                    "id": issue.id,
                    "iid": issue.iid,
                    "title": issue.title,
                    "state": issue.state,
                    "labels": issue.labels,
                    "web_url": issue.web_url,
                }
                for issue in issues
            ],
            "total": len(issues),
            "page": page,
            "per_page": per_page,
        }

    # Run sync code in thread pool
    return await asyncio.to_thread(_sync_list)
