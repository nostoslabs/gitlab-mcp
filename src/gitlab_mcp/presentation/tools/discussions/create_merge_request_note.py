"""Create a comment (note) on a GitLab merge request."""

import asyncio
from typing import Any

from fastmcp import Context
from gitlab_mcp.presentation.tools.common.helpers import get_user_context
from gitlab_mcp.services.gitlab_client_factory import GitLabClientFactory

# Module-level instances (will be injected by server)
client_factory = GitLabClientFactory()


async def create_merge_request_note(
    project_id: str,
    mr_iid: int,
    body: str,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Create a comment (note) on a GitLab merge request.

    Args:
        project_id: Project ID or path (e.g., "gitlab-org/gitlab" or "123")
        mr_iid: Merge request IID (internal ID)
        body: Comment text (markdown supported)
        ctx: FastMCP context for multi-tenant support

    Returns:
        Dictionary containing the created note:
        - id: Note ID
        - body: Note body text
        - author: Author information (id, username, name)
        - created_at: Creation timestamp
        - updated_at: Last update timestamp
        - system: Whether this is a system note
        - noteable_id: ID of the noteable object (merge request)
        - noteable_type: Type of the noteable object

    Example:
        >>> result = await create_merge_request_note("my-project", 123, "LGTM!")
    """

    def _sync_create_merge_request_note() -> dict[str, Any]:
        user_ctx = get_user_context(ctx)
        gl = client_factory.get_client(user_ctx)

        # Get the project
        try:
            project = gl.projects.get(project_id)
        except Exception as e:
            raise ValueError(f"Project '{project_id}' not found: {e}")

        # Get the merge request
        try:
            mr = project.mergerequests.get(mr_iid)
        except Exception as e:
            raise ValueError(f"Merge request '{mr_iid}' not found: {e}")

        # Create the note
        note = mr.notes.create({"body": body})

        # Serialize note
        note_data = {
            "id": note.id,
            "body": note.body,
            "created_at": getattr(note, "created_at", None),
            "updated_at": getattr(note, "updated_at", None),
            "system": getattr(note, "system", False),
            "noteable_id": getattr(note, "noteable_id", None),
            "noteable_type": getattr(note, "noteable_type", None),
        }

        # Add author information if available
        if hasattr(note, "author") and note.author:
            note_data["author"] = {
                "id": getattr(note.author, "id", None),
                "username": getattr(note.author, "username", None),
                "name": getattr(note.author, "name", None),
            }

        return note_data

    return await asyncio.to_thread(_sync_create_merge_request_note)
