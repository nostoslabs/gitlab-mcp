"""Approve merge request tool."""

import asyncio
from typing import Any

import gitlab
from fastmcp import Context
from gitlab_mcp.presentation.tools.common.helpers import get_user_context
from gitlab_mcp.services.gitlab_client_factory import GitLabClientFactory

# Module-level instances (will be injected by server)
client_factory = GitLabClientFactory()


async def approve_merge_request(
    project_id: str,
    mr_iid: int,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Approve a merge request.

    Args:
        project_id: GitLab project ID or path
        mr_iid: Merge request IID
        ctx: FastMCP context

    Returns:
        Approval details including approved status and approved_by list

    Raises:
        ValueError: If project or merge request not found
        gitlab.exceptions.GitlabError: If approval fails
    """

    def _sync_approve() -> dict[str, Any]:
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

        # 5. Approve the merge request
        approval = mr.approve()

        # 6. Return serialized response
        return {
            "id": getattr(approval, "id"),
            "iid": getattr(approval, "iid"),
            "approved": getattr(approval, "approved"),
            "approved_by": getattr(approval, "approved_by"),
        }

    # Run sync code in thread pool (python-gitlab is sync, FastMCP is async)
    return await asyncio.to_thread(_sync_approve)
