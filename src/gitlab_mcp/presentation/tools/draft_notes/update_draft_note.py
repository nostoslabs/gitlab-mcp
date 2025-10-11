"""Update a draft note on a merge request in GitLab."""

import asyncio
from typing import Any

from fastmcp import Context
from gitlab_mcp.presentation.tools.common.helpers import get_user_context
from gitlab_mcp.services.gitlab_client_factory import GitLabClientFactory

# Module-level instances (will be injected by server)
client_factory = GitLabClientFactory()


async def update_draft_note(
    project_id: str,
    mr_iid: int,
    draft_note_id: int,
    note: str | None = None,
    position: dict[str, Any] | None = None,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Update a draft note (unpublished comment) on a merge request.

    Args:
        project_id: Project ID or path
        mr_iid: Merge request IID (internal ID)
        draft_note_id: Draft note ID
        note: New draft note content
        position: New position info for inline comments (optional)
        ctx: FastMCP context for multi-tenant support

    Returns:
        Dictionary containing updated draft note details

    Example:
        >>> result = await update_draft_note("my-project", 123, 456, note="Updated review comment")
    """

    def _sync_update_draft_note() -> dict[str, Any]:
        user_ctx = get_user_context(ctx)
        gl = client_factory.get_client(user_ctx)

        # Get the project, merge request, and draft note
        try:
            project = gl.projects.get(project_id)
            mr = project.mergerequests.get(mr_iid)
            draft = mr.draftnotes.get(draft_note_id)
        except Exception as e:
            raise ValueError(f"Draft note '{draft_note_id}' not found: {e}")

        # Update draft note
        try:
            if note:
                draft.note = note
            if position:
                draft.position = position
            draft.save()
        except Exception as e:
            raise ValueError(f"Failed to update draft note: {e}")

        # Serialize draft note
        return {
            "id": draft.id,
            "author": {
                "id": getattr(draft.author, "id", None) if hasattr(draft, "author") else None,
                "username": (
                    getattr(draft.author, "username", None) if hasattr(draft, "author") else None
                ),
                "name": getattr(draft.author, "name", None) if hasattr(draft, "author") else None,
            },
            "note": draft.note,
            "position": getattr(draft, "position", None),
            "created_at": getattr(draft, "created_at", None),
            "updated_at": getattr(draft, "updated_at", None),
        }

    return await asyncio.to_thread(_sync_update_draft_note)
