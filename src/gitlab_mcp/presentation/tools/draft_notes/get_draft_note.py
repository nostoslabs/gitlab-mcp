"""Get details of a specific draft note on a GitLab merge request."""

import asyncio
from typing import Any

from fastmcp import Context
from gitlab_mcp.presentation.tools.common.helpers import get_user_context
from gitlab_mcp.services.gitlab_client_factory import GitLabClientFactory

# Module-level instances (will be injected by server)
client_factory = GitLabClientFactory()


async def get_draft_note(
    project_id: str,
    mr_iid: int,
    draft_note_id: int,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Get details of a specific draft note on a GitLab merge request.

    Args:
        project_id: Project ID or path (e.g., "gitlab-org/gitlab" or "123")
        mr_iid: Merge request IID (internal ID)
        draft_note_id: Draft note ID
        ctx: FastMCP context for multi-tenant support

    Returns:
        Dictionary containing draft note details:
        - id: Draft note ID
        - note: Note text
        - author: Author information
        - position: Position information (for line comments)
        - resolve_discussion: Whether this note resolves a discussion

    Example:
        >>> result = await get_draft_note("my-project", 42, 123)
    """

    def _sync_get_draft_note() -> dict[str, Any]:
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

        # Get the draft note
        try:
            note = mr.draft_notes.get(draft_note_id)
        except AttributeError:
            raise ValueError(
                "Draft notes feature not available. This may require a newer GitLab version."
            )
        except Exception as e:
            raise ValueError(f"Draft note '{draft_note_id}' not found: {e}")

        # Serialize draft note
        note_data = {
            "id": note.id,
            "note": getattr(note, "note", None),
            "author": {},
            "position": None,
            "resolve_discussion": getattr(note, "resolve_discussion", False),
        }

        # Add author information if available
        if hasattr(note, "author") and note.author:
            note_data["author"] = {
                "id": (
                    note.author.get("id")
                    if isinstance(note.author, dict)
                    else getattr(note.author, "id", None)
                ),
                "username": (
                    note.author.get("username")
                    if isinstance(note.author, dict)
                    else getattr(note.author, "username", None)
                ),
                "name": (
                    note.author.get("name")
                    if isinstance(note.author, dict)
                    else getattr(note.author, "name", None)
                ),
            }

        # Add position information if this is a line comment
        if hasattr(note, "position") and note.position:
            position = note.position
            note_data["position"] = {
                "base_sha": (
                    position.get("base_sha")
                    if isinstance(position, dict)
                    else getattr(position, "base_sha", None)
                ),
                "start_sha": (
                    position.get("start_sha")
                    if isinstance(position, dict)
                    else getattr(position, "start_sha", None)
                ),
                "head_sha": (
                    position.get("head_sha")
                    if isinstance(position, dict)
                    else getattr(position, "head_sha", None)
                ),
                "old_path": (
                    position.get("old_path")
                    if isinstance(position, dict)
                    else getattr(position, "old_path", None)
                ),
                "new_path": (
                    position.get("new_path")
                    if isinstance(position, dict)
                    else getattr(position, "new_path", None)
                ),
                "old_line": (
                    position.get("old_line")
                    if isinstance(position, dict)
                    else getattr(position, "old_line", None)
                ),
                "new_line": (
                    position.get("new_line")
                    if isinstance(position, dict)
                    else getattr(position, "new_line", None)
                ),
            }

        return note_data

    return await asyncio.to_thread(_sync_get_draft_note)
