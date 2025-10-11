"""Publish a draft note (convert to a regular comment) on a merge request."""

import asyncio
from typing import Any

from fastmcp import Context
from gitlab_mcp.presentation.tools.common.helpers import get_user_context
from gitlab_mcp.services.gitlab_client_factory import GitLabClientFactory

# Module-level instances (will be injected by server)
client_factory = GitLabClientFactory()


async def publish_draft_note(
    project_id: str,
    mr_iid: int,
    draft_note_id: int,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Publish a draft note (convert it to a regular comment).

    Args:
        project_id: Project ID or path
        mr_iid: Merge request IID (internal ID)
        draft_note_id: Draft note ID to publish
        ctx: FastMCP context for multi-tenant support

    Returns:
        Dictionary containing published note details

    Example:
        >>> result = await publish_draft_note("my-project", 123, 456)
    """

    def _sync_publish_draft_note() -> dict[str, Any]:
        user_ctx = get_user_context(ctx)
        gl = client_factory.get_client(user_ctx)

        # Get the project, merge request, and draft note
        try:
            project = gl.projects.get(project_id)
            mr = project.mergerequests.get(mr_iid)
            mr.draftnotes.get(draft_note_id)
        except Exception as e:
            raise ValueError(f"Draft note '{draft_note_id}' not found: {e}")

        # Publish the draft note
        try:
            # Publishing a draft note in GitLab API is done by calling the publish endpoint
            # The python-gitlab library doesn't have a direct publish method,
            # so we use the manager's custom action
            mr.draftnotes.publish(draft_note_id)
        except Exception as e:
            raise ValueError(f"Failed to publish draft note: {e}")

        return {
            "success": True,
            "message": f"Draft note {draft_note_id} published successfully",
            "published_draft_note_id": draft_note_id,
            "mr_iid": mr_iid,
        }

    return await asyncio.to_thread(_sync_publish_draft_note)
