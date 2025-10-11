"""Merge merge request tool."""

import asyncio
from typing import Any

import gitlab
from fastmcp import Context
from gitlab_mcp.presentation.tools.common.helpers import get_user_context
from gitlab_mcp.services.gitlab_client_factory import GitLabClientFactory

# Module-level instances (will be injected by server)
client_factory = GitLabClientFactory()


async def merge_merge_request(
    project_id: str,
    mr_iid: int,
    merge_commit_message: str | None = None,
    should_remove_source_branch: bool = False,
    squash: bool = False,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Merge a merge request.

    Args:
        project_id: GitLab project ID or path
        mr_iid: Merge request IID
        merge_commit_message: Custom merge commit message
        should_remove_source_branch: Delete source branch after merge
        squash: Squash commits when merging
        ctx: FastMCP context

    Returns:
        Merged merge request details

    Raises:
        ValueError: If project or merge request not found
        gitlab.exceptions.GitlabMRClosedError: If MR is already closed/merged
    """

    def _sync_merge() -> dict[str, Any]:
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

        # 5. Merge using python-gitlab
        merge_params: dict[str, Any] = {
            "should_remove_source_branch": should_remove_source_branch,
            "squash": squash,
        }
        if merge_commit_message:
            merge_params["merge_commit_message"] = merge_commit_message

        mr.merge(**merge_params)

        # 6. Refresh to get latest state
        mr = project.mergerequests.get(mr_iid)

        # 7. Return serialized response
        return {
            "id": mr.id,
            "iid": mr.iid,
            "title": mr.title,
            "state": mr.state,
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
            "web_url": mr.web_url,
        }

    # Run sync code in thread pool (python-gitlab is sync, FastMCP is async)
    return await asyncio.to_thread(_sync_merge)
