"""List discussions (comments) on a GitLab issue."""

import asyncio
from typing import Any

from fastmcp import Context
from gitlab_mcp.presentation.tools.common.helpers import get_user_context
from gitlab_mcp.services.gitlab_client_factory import GitLabClientFactory

# Module-level instances (will be injected by server)
client_factory = GitLabClientFactory()


async def list_issue_discussions(
    project_id: str,
    issue_iid: int,
    page: int = 1,
    per_page: int = 20,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """List all discussions (comments) on a GitLab issue.

    Args:
        project_id: Project ID or path (e.g., "gitlab-org/gitlab" or "123")
        issue_iid: Issue IID (internal ID)
        page: Page number for pagination (default: 1)
        per_page: Number of discussions per page (default: 20, max: 100)
        ctx: FastMCP context for multi-tenant support

    Returns:
        Dictionary containing:
        - discussions: List of discussion objects with notes
        - total_results: Total number of discussions returned

    Example:
        >>> result = await list_issue_discussions("my-project", 42)
        >>> result = await list_issue_discussions("my-project", 42, page=2, per_page=50)
    """

    def _sync_list_issue_discussions() -> dict[str, Any]:
        user_ctx = get_user_context(ctx)
        gl = client_factory.get_client(user_ctx)

        # Get the project
        try:
            project = gl.projects.get(project_id)
        except Exception as e:
            raise ValueError(f"Project '{project_id}' not found: {e}")

        # Get the issue
        try:
            issue = project.issues.get(issue_iid)
        except Exception as e:
            raise ValueError(f"Issue '{issue_iid}' not found: {e}")

        # Get discussions
        discussions_list = issue.discussions.list(page=page, per_page=per_page)

        # Serialize discussions
        discussions = []
        for discussion in discussions_list:
            discussion_data = {
                "id": discussion.id,
                "individual_note": getattr(discussion, "individual_note", False),
                "notes": [],
            }

            # Serialize notes in the discussion
            if hasattr(discussion, "attributes") and "notes" in discussion.attributes:
                for note in discussion.attributes["notes"]:
                    note_data = {
                        "id": note.get("id"),
                        "body": note.get("body"),
                        "created_at": note.get("created_at"),
                        "updated_at": note.get("updated_at"),
                        "system": note.get("system", False),
                        "noteable_id": note.get("noteable_id"),
                        "noteable_type": note.get("noteable_type"),
                    }

                    # Add author information if available
                    if "author" in note and note["author"]:
                        note_data["author"] = {
                            "id": note["author"].get("id"),
                            "username": note["author"].get("username"),
                            "name": note["author"].get("name"),
                        }

                    discussion_data["notes"].append(note_data)

            discussions.append(discussion_data)

        return {
            "discussions": discussions,
            "total_results": len(discussions),
        }

    return await asyncio.to_thread(_sync_list_issue_discussions)
