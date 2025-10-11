"""Update issue tool."""

import asyncio
from typing import Any

import gitlab
from fastmcp import Context
from gitlab_mcp.presentation.tools.common.helpers import get_user_context
from gitlab_mcp.services.gitlab_client_factory import GitLabClientFactory

# Module-level instances (will be injected by server)
client_factory = GitLabClientFactory()


async def update_issue(
    project_id: str,
    issue_iid: int,
    title: str | None = None,
    description: str | None = None,
    labels: list[str] | None = None,
    state_event: str | None = None,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Update an existing issue in a GitLab project.

    Args:
        project_id: GitLab project ID or namespace/project path
        issue_iid: Issue IID (project-scoped ID)
        title: New issue title
        description: New issue description in markdown
        labels: New list of label names (replaces existing)
        state_event: State transition ('close' or 'reopen')
        ctx: FastMCP context (auto-injected)

    Returns:
        Updated issue details

    Raises:
        ValueError: If project or issue not found
        gitlab.exceptions.GitlabUpdateError: If update fails
    """

    def _sync_update() -> dict[str, Any]:
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

        # 5. Update issue attributes
        if title is not None:
            issue.title = title
        if description is not None:
            issue.description = description
        if labels is not None:
            issue.labels = labels
        if state_event is not None:
            issue.state_event = state_event

        # 6. Save changes
        issue.save()

        # 7. Return serialized response
        return {
            "id": issue.id,
            "iid": issue.iid,
            "project_id": issue.project_id,
            "title": issue.title,
            "description": issue.description,
            "state": issue.state,
            "labels": issue.labels,
            "web_url": issue.web_url,
            "updated_at": issue.updated_at,
        }

    # Run sync code in thread pool
    return await asyncio.to_thread(_sync_update)
