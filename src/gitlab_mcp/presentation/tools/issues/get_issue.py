"""Get issue tool."""

import asyncio
from typing import Any

import gitlab
from fastmcp import Context
from gitlab_mcp.presentation.tools.common.helpers import get_user_context
from gitlab_mcp.services.gitlab_client_factory import GitLabClientFactory

# Module-level instances (will be injected by server)
client_factory = GitLabClientFactory()


async def get_issue(
    project_id: str,
    issue_iid: int,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Get a specific issue by IID.

    Args:
        project_id: GitLab project ID or namespace/project path
        issue_iid: Issue IID (project-scoped ID)
        ctx: FastMCP context (auto-injected)

    Returns:
        Issue details including id, iid, title, state, assignees, etc.

    Raises:
        ValueError: If project or issue not found
        gitlab.exceptions.GitlabGetError: If retrieval fails
    """

    def _sync_get() -> dict[str, Any]:
        # 1. Get user context
        user_ctx = get_user_context(ctx)

        # 2. Get GitLab client for this user
        gl = client_factory.get_client(user_ctx)

        # 3. Get project
        try:
            project = gl.projects.get(project_id)
        except gitlab.exceptions.GitlabGetError as e:
            raise ValueError(f"Project {project_id} not found") from e

        # 4. Get issue
        try:
            issue = project.issues.get(issue_iid)
        except gitlab.exceptions.GitlabGetError as e:
            raise ValueError(f"Issue {issue_iid} not found in project {project_id}") from e

        # 5. Return serialized response
        return {
            "id": issue.id,
            "iid": issue.iid,
            "project_id": issue.project_id,
            "title": issue.title,
            "description": issue.description,
            "state": issue.state,
            "labels": issue.labels,
            "web_url": issue.web_url,
            "assignees": [{"username": a["username"], "name": a["name"]} for a in issue.assignees],
            "created_at": issue.created_at,
            "updated_at": issue.updated_at,
        }

    # Run sync code in thread pool
    return await asyncio.to_thread(_sync_get)
