"""Update a note/comment on an issue in GitLab."""

import asyncio
from typing import Any

from fastmcp import Context
from gitlab_mcp.presentation.tools.common.helpers import get_user_context
from gitlab_mcp.services.gitlab_client_factory import GitLabClientFactory

# Module-level instances (will be injected by server)
client_factory = GitLabClientFactory()


async def update_issue_note(
    project_id: str,
    issue_iid: int,
    note_id: int,
    body: str,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Update a note/comment on an issue in GitLab.

    Args:
        project_id: Project ID or path
        issue_iid: Issue IID (internal ID)
        note_id: Note ID to update
        body: New note content
        ctx: FastMCP context for multi-tenant support

    Returns:
        Dictionary containing updated note details

    Example:
        >>> result = await update_issue_note("my-project", 123, 456, "Updated comment text")
    """

    def _sync_update_issue_note() -> dict[str, Any]:
        user_ctx = get_user_context(ctx)
        gl = client_factory.get_client(user_ctx)

        # Get the project, issue, and note
        try:
            project = gl.projects.get(project_id)
            issue = project.issues.get(issue_iid)
            note = issue.notes.get(note_id)
        except Exception as e:
            raise ValueError(f"Note '{note_id}' on issue '{project_id}#{issue_iid}' not found: {e}")

        # Update the note
        try:
            note.body = body
            note.save()
        except Exception as e:
            raise ValueError(f"Failed to update issue note: {e}")

        # Serialize note
        return {
            "id": note.id,
            "body": note.body,
            "author": {
                "id": getattr(note.author, "id", None) if hasattr(note, "author") else None,
                "username": (
                    getattr(note.author, "username", None) if hasattr(note, "author") else None
                ),
                "name": getattr(note.author, "name", None) if hasattr(note, "author") else None,
            },
            "created_at": getattr(note, "created_at", None),
            "updated_at": getattr(note, "updated_at", None),
            "system": getattr(note, "system", False),
            "noteable_type": getattr(note, "noteable_type", None),
            "noteable_iid": issue_iid,
        }

    return await asyncio.to_thread(_sync_update_issue_note)
