"""Create issue tool."""

import asyncio
from typing import Any

import gitlab
from fastmcp import Context
from gitlab_mcp.presentation.tools.common.helpers import get_user_context
from gitlab_mcp.services.gitlab_client_factory import GitLabClientFactory

# Module-level instances (will be injected by server)
client_factory = GitLabClientFactory()


async def create_issue(
    project_id: str,
    title: str,
    description: str | None = None,
    labels: list[str] | None = None,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Create a new issue in a GitLab project.

    Args:
        project_id: GitLab project ID or namespace/project path
        title: Issue title (required)
        description: Issue description in markdown
        labels: List of label names to apply
        ctx: FastMCP context (auto-injected)

    Returns:
        Created issue details including id, iid, title, state, web_url, etc.

    Raises:
        ValueError: If project not found or token missing
        gitlab.exceptions.GitlabCreateError: If issue creation fails
    """

    def _sync_create() -> dict[str, Any]:
        # 1. Get user context (multi-tenant) or use default
        user_ctx = get_user_context(ctx)

        # 2. Get GitLab client for this user
        gl = client_factory.get_client(user_ctx)

        # 3. Get project using python-gitlab
        try:
            project = gl.projects.get(project_id)
        except gitlab.exceptions.GitlabGetError as e:
            raise ValueError(f"Project {project_id} not found") from e

        # 4. Create issue - python-gitlab handles API call
        issue_data: dict[str, Any] = {
            "title": title,
        }
        if description:
            issue_data["description"] = description
        if labels:
            issue_data["labels"] = ",".join(labels)

        issue = project.issues.create(issue_data)

        # 5. Return serialized response (python-gitlab object → dict)
        return {
            "id": issue.id,
            "iid": issue.iid,
            "project_id": issue.project_id,
            "title": issue.title,
            "description": issue.description,
            "state": issue.state,
            "labels": issue.labels,
            "web_url": issue.web_url,
            "created_at": issue.created_at,
            "updated_at": issue.updated_at,
            "author": (
                {"username": issue.author["username"], "name": issue.author["name"]}
                if issue.author
                else None
            ),
        }

    # Run sync code in thread pool (python-gitlab is sync, FastMCP is async)
    return await asyncio.to_thread(_sync_create)
