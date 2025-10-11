"""List discussions on a merge request in GitLab."""

import asyncio
from typing import Any

from fastmcp import Context
from gitlab_mcp.presentation.tools.common.helpers import get_user_context
from gitlab_mcp.services.gitlab_client_factory import GitLabClientFactory

# Module-level instances (will be injected by server)
client_factory = GitLabClientFactory()


async def list_merge_request_discussions(
    project_id: str,
    mr_iid: int,
    page: int = 1,
    per_page: int = 20,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """List discussions (comment threads) on a merge request.

    Args:
        project_id: Project ID or path
        mr_iid: Merge request IID (internal ID)
        page: Page number for pagination (default: 1)
        per_page: Number of discussions per page (default: 20, max: 100)
        ctx: FastMCP context for multi-tenant support

    Returns:
        Dictionary containing list of discussions with pagination info

    Example:
        >>> result = await list_merge_request_discussions("my-project", 123)
    """

    def _sync_list_mr_discussions() -> dict[str, Any]:
        user_ctx = get_user_context(ctx)
        gl = client_factory.get_client(user_ctx)

        # Get the project and merge request
        try:
            project = gl.projects.get(project_id)
            mr = project.mergerequests.get(mr_iid)
        except Exception as e:
            raise ValueError(f"Merge request '{project_id}!{mr_iid}' not found: {e}")

        # Get discussions with pagination
        try:
            discussions_list = mr.discussions.list(page=page, per_page=per_page, get_all=False)
        except Exception as e:
            raise ValueError(f"Failed to fetch discussions: {e}")

        # Serialize discussions
        discussions_data = []
        for discussion in discussions_list:
            notes = []
            if hasattr(discussion, "attributes") and "notes" in discussion.attributes:
                for note in discussion.attributes["notes"]:
                    notes.append(
                        {
                            "id": note.get("id"),
                            "body": note.get("body"),
                            "author": (
                                {
                                    "id": note.get("author", {}).get("id"),
                                    "username": note.get("author", {}).get("username"),
                                    "name": note.get("author", {}).get("name"),
                                }
                                if note.get("author")
                                else None
                            ),
                            "created_at": note.get("created_at"),
                            "updated_at": note.get("updated_at"),
                            "system": note.get("system", False),
                            "resolvable": note.get("resolvable", False),
                            "resolved": note.get("resolved", False),
                        }
                    )

            discussions_data.append(
                {
                    "id": discussion.id,
                    "individual_note": getattr(discussion, "individual_note", False),
                    "notes": notes,
                }
            )

        return {
            "discussions": discussions_data,
            "total_results": len(discussions_data),
            "page": page,
            "per_page": per_page,
            "mr_iid": mr_iid,
        }

    return await asyncio.to_thread(_sync_list_mr_discussions)
