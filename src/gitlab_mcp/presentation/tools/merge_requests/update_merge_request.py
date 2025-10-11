"""Update a merge request in GitLab."""

import asyncio
from typing import Any

from fastmcp import Context
from gitlab_mcp.presentation.tools.common.helpers import get_user_context
from gitlab_mcp.services.gitlab_client_factory import GitLabClientFactory

# Module-level instances (will be injected by server)
client_factory = GitLabClientFactory()


async def update_merge_request(
    project_id: str,
    mr_iid: int,
    title: str | None = None,
    description: str | None = None,
    state_event: str | None = None,
    target_branch: str | None = None,
    assignee_ids: list[int] | None = None,
    reviewer_ids: list[int] | None = None,
    labels: list[str] | None = None,
    milestone_id: int | None = None,
    remove_source_branch: bool | None = None,
    squash: bool | None = None,
    draft: bool | None = None,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Update a merge request in GitLab.

    Args:
        project_id: Project ID or path
        mr_iid: Merge request IID (internal ID)
        title: New merge request title
        description: New merge request description
        state_event: State change ('close', 'reopen', 'merge')
        target_branch: New target branch
        assignee_ids: List of assignee user IDs
        reviewer_ids: List of reviewer user IDs
        labels: List of label names
        milestone_id: Milestone ID
        remove_source_branch: Remove source branch after merge
        squash: Squash commits when merging
        draft: Mark as draft/WIP
        ctx: FastMCP context for multi-tenant support

    Returns:
        Dictionary containing updated merge request details

    Example:
         >>> result = await update_merge_request("my-project", 123, title="Updated title")
    """

    def _sync_update_merge_request() -> dict[str, Any]:
        user_ctx = get_user_context(ctx)
        gl = client_factory.get_client(user_ctx)

        # Get the project and merge request
        try:
            project = gl.projects.get(project_id)
            mr = project.mergerequests.get(mr_iid)
        except Exception as e:
            raise ValueError(f"Merge request '{project_id}!{mr_iid}' not found: {e}")

        # Update merge request attributes
        try:
            if title is not None:
                mr.title = title
            if description is not None:
                mr.description = description
            if state_event is not None:
                mr.state_event = state_event
            if target_branch is not None:
                mr.target_branch = target_branch
            if assignee_ids is not None:
                mr.assignee_ids = assignee_ids
            if reviewer_ids is not None:
                mr.reviewer_ids = reviewer_ids
            if labels is not None:
                mr.labels = labels
            if milestone_id is not None:
                mr.milestone_id = milestone_id
            if remove_source_branch is not None:
                mr.remove_source_branch = remove_source_branch
            if squash is not None:
                mr.squash = squash
            if draft is not None:
                mr.draft = draft

            mr.save()
        except Exception as e:
            raise ValueError(f"Failed to update merge request: {e}")

        # Serialize merge request
        return {
            "iid": mr.iid,
            "id": mr.id,
            "title": mr.title,
            "description": getattr(mr, "description", None),
            "state": mr.state,
            "draft": getattr(mr, "draft", False),
            "source_branch": mr.source_branch,
            "target_branch": mr.target_branch,
            "author": {
                "id": getattr(mr.author, "id", None) if hasattr(mr, "author") else None,
                "username": getattr(mr.author, "username", None) if hasattr(mr, "author") else None,
            },
            "assignees": (
                [
                    {"id": assignee.get("id"), "username": assignee.get("username")}
                    for assignee in getattr(mr, "assignees", [])
                ]
                if hasattr(mr, "assignees") and mr.assignees
                else []
            ),
            "labels": getattr(mr, "labels", []),
            "web_url": getattr(mr, "web_url", None),
            "created_at": getattr(mr, "created_at", None),
            "updated_at": getattr(mr, "updated_at", None),
        }

    return await asyncio.to_thread(_sync_update_merge_request)
