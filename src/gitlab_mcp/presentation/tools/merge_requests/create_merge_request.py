"""Create merge request tool."""

import asyncio
from typing import Any

import gitlab
from fastmcp import Context
from gitlab_mcp.presentation.tools.common.helpers import get_user_context
from gitlab_mcp.services.gitlab_client_factory import GitLabClientFactory

# Module-level instances (will be injected by server)
client_factory = GitLabClientFactory()


async def create_merge_request(
    project_id: str,
    source_branch: str,
    target_branch: str,
    title: str,
    description: str | None = None,
    assignee_id: int | None = None,
    labels: list[str] | None = None,
    remove_source_branch: bool = False,
    squash: bool = False,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Create a new merge request.

    Args:
        project_id: GitLab project ID or namespace/project path
        source_branch: Source branch name
        target_branch: Target branch name
        title: MR title (required)
        description: MR description in markdown
        assignee_id: User ID to assign MR to
        labels: List of label names
        remove_source_branch: Delete source branch when merged
        squash: Squash commits when merging
        ctx: FastMCP context (auto-injected)

    Returns:
        Created merge request details including id, iid, title, state, web_url, etc.

    Raises:
        ValueError: If project not found or token missing
        gitlab.exceptions.GitlabCreateError: If MR creation fails
    """

    def _sync_create() -> dict[str, Any]:
        # 1. Get user context
        user_ctx = get_user_context(ctx)

        # 2. Get GitLab client for user
        gl = client_factory.get_client(user_ctx)

        # 3. Get project
        try:
            project = gl.projects.get(project_id)
        except gitlab.exceptions.GitlabGetError as e:
            raise ValueError(f"Project '{project_id}' not found") from e

        # 4. Build MR data
        mr_data: dict[str, Any] = {
            "source_branch": source_branch,
            "target_branch": target_branch,
            "title": title,
            "remove_source_branch": remove_source_branch,
            "squash": squash,
        }

        if description:
            mr_data["description"] = description
        if assignee_id:
            mr_data["assignee_id"] = assignee_id
        if labels:
            mr_data["labels"] = ",".join(labels)

        # 5. Create merge request using python-gitlab
        mr = project.mergerequests.create(mr_data)

        # 6. Return serialized response
        return {
            "id": mr.id,
            "iid": mr.iid,
            "project_id": mr.project_id,
            "title": mr.title,
            "description": mr.description,
            "state": mr.state,
            "source_branch": mr.source_branch,
            "target_branch": mr.target_branch,
            "author": (
                {
                    "id": mr.author["id"],
                    "username": mr.author["username"],
                    "name": mr.author["name"],
                }
                if mr.author
                else None
            ),
            "assignee": (
                {
                    "id": mr.assignee["id"],
                    "username": mr.assignee["username"],
                    "name": mr.assignee["name"],
                }
                if mr.assignee
                else None
            ),
            "labels": mr.labels,
            "web_url": mr.web_url,
            "created_at": mr.created_at,
            "updated_at": mr.updated_at,
            "merge_status": mr.merge_status,
            "has_conflicts": mr.has_conflicts,
            "work_in_progress": mr.work_in_progress,
        }

    # Run sync code in thread pool (python-gitlab is sync, FastMCP is async)
    return await asyncio.to_thread(_sync_create)
