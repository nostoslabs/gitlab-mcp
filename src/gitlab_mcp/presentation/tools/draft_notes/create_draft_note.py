"""Create a draft note on a merge request in GitLab."""

import asyncio
from typing import Any

from fastmcp import Context
from gitlab_mcp.presentation.tools.common.helpers import get_user_context
from gitlab_mcp.services.gitlab_client_factory import GitLabClientFactory

# Module-level instances (will be injected by server)
client_factory = GitLabClientFactory()


async def create_draft_note(
    project_id: str,
    mr_iid: int,
    note: str,
    position: dict[str, Any] | None = None,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Create a draft note (unpublished comment) on a merge request.

    Args:
        project_id: Project ID or path
        mr_iid: Merge request IID (internal ID)
        note: Draft note content
        position: Position info for inline comments (optional):
            - base_sha: Base commit SHA
            - head_sha: Head commit SHA
            - start_sha: Start commit SHA
            - new_path: Path to file
            - new_line: Line number
            - old_path: Old path (for moved files)
            - old_line: Old line number
        ctx: FastMCP context for multi-tenant support

    Returns:
        Dictionary containing created draft note details

    Example:
        >>> result = await create_draft_note("my-project", 123, "This needs review")
    """

    def _sync_create_draft_note() -> dict[str, Any]:
        user_ctx = get_user_context(ctx)
        gl = client_factory.get_client(user_ctx)

        # Get the project and merge request
        try:
            project = gl.projects.get(project_id)
            mr = project.mergerequests.get(mr_iid)
        except Exception as e:
            raise ValueError(f"Merge request '{project_id}!{mr_iid}' not found: {e}")

        # Build draft note data
        draft_data: dict[str, Any] = {
            "note": note,
        }

        if position:
            draft_data["position"] = position

        # Create the draft note
        try:
            draft = mr.draftnotes.create(draft_data)
        except Exception as e:
            raise ValueError(f"Failed to create draft note: {e}")

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

    return await asyncio.to_thread(_sync_create_draft_note)
