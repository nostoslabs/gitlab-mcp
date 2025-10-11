"""Get merge request tool."""

import asyncio
from typing import Any

import gitlab
from fastmcp import Context
from gitlab_mcp.presentation.tools.common.helpers import get_user_context
from gitlab_mcp.services.gitlab_client_factory import GitLabClientFactory

# Module-level instances (will be injected by server)
client_factory = GitLabClientFactory()


async def get_merge_request(
    project_id: str,
    mr_iid: int,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Get a specific merge request by IID.

    Args:
        project_id: GitLab project ID or path
        mr_iid: Merge request IID (project-scoped ID)
        ctx: FastMCP context

    Returns:
        Merge request details including id, iid, title, state, web_url, etc.

    Raises:
        ValueError: If project or merge request not found
        gitlab.exceptions.GitlabGetError: If retrieval fails
    """

    def _sync_get() -> dict[str, Any]:
        # 1. Get user context
        user_ctx = get_user_context(ctx)

        # 2. Get GitLab client
        gl = client_factory.get_client(user_ctx)

        # 3. Get project
        try:
            project = gl.projects.get(project_id)
        except gitlab.exceptions.GitlabGetError as e:
            raise ValueError(f"Project '{project_id}' not found") from e

        # 4. Get merge request
        try:
            mr = project.mergerequests.get(mr_iid)
        except gitlab.exceptions.GitlabGetError as e:
            raise ValueError(f"Merge request {mr_iid} not found in project '{project_id}'") from e

        # 5. Return serialized response
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
            "merged_by": (
                {
                    "id": mr.merged_by["id"],
                    "username": mr.merged_by["username"],
                    "name": mr.merged_by["name"],
                }
                if mr.merged_by
                else None
            ),
            "merged_at": mr.merged_at,
        }

    # Run sync code in thread pool (python-gitlab is sync, FastMCP is async)
    return await asyncio.to_thread(_sync_get)
