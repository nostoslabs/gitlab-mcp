"""List draft notes (comments) on a GitLab merge request."""

import asyncio
from typing import Any

from fastmcp import Context
from gitlab_mcp.presentation.tools.common.helpers import get_user_context
from gitlab_mcp.services.gitlab_client_factory import GitLabClientFactory

# Module-level instances (will be injected by server)
client_factory = GitLabClientFactory()


async def list_draft_notes(
    project_id: str,
    mr_iid: int,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """List draft notes (unpublished comments) on a GitLab merge request.

    Draft notes are comments that have been written but not yet published.
    They allow reviewers to compose multiple comments before submitting them all at once.

    Args:
        project_id: Project ID or path (e.g., "gitlab-org/gitlab" or "123")
        mr_iid: Merge request IID (internal ID)
        ctx: FastMCP context for multi-tenant support

    Returns:
        Dictionary containing:
        - draft_notes: List of draft note objects
        - total_results: Total number of draft notes returned

    Example:
        >>> result = await list_draft_notes("my-project", 42)
    """

    def _sync_list_draft_notes() -> dict[str, Any]:
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

        # Get draft notes (this may not be available in all GitLab versions)
        try:
            draft_notes_list = mr.draft_notes.list()
        except AttributeError:
            # If draft_notes are not available
            return {
                "draft_notes": [],
                "total_results": 0,
                "message": "Draft notes feature not available. Requires newer GitLab version.",
            }
        except Exception as e:
            raise ValueError(f"Failed to retrieve draft notes: {e}")

        # Serialize draft notes
        draft_notes = []
        for note in draft_notes_list:
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

            draft_notes.append(note_data)

        return {
            "draft_notes": draft_notes,
            "total_results": len(draft_notes),
        }

    return await asyncio.to_thread(_sync_list_draft_notes)
