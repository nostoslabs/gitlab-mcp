"""List diffs for a merge request with pagination."""

import asyncio
from typing import Any

from fastmcp import Context
from gitlab_mcp.presentation.tools.common.helpers import get_user_context
from gitlab_mcp.services.gitlab_client_factory import GitLabClientFactory

# Module-level instances (will be injected by server)
client_factory = GitLabClientFactory()


async def list_merge_request_diffs(
    project_id: str,
    mr_iid: int,
    page: int = 1,
    per_page: int = 20,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """List diffs for a merge request with pagination.

    Returns the changes introduced by the merge request, showing additions and
    deletions for each modified file. Supports pagination for large merge requests.

    Args:
        project_id: Project ID or path (e.g., "gitlab-org/gitlab" or "123")
        mr_iid: Merge request IID (project-scoped ID)
        page: Page number for pagination (default: 1)
        per_page: Number of diffs per page (default: 20, max: 100)
        ctx: FastMCP context for multi-tenant support

    Returns:
        Dictionary containing:
        - mr_iid: The merge request IID
        - diffs: List of diff objects (paginated)
        - total_results: Number of diffs returned in this page

    Example:
        >>> diffs = await list_merge_request_diffs("gitlab-org/gitlab", 123, per_page=10)
        >>> diffs = await list_merge_request_diffs("my-org/my-project", 45, page=2)
    """

    def _sync_list_merge_request_diffs() -> dict[str, Any]:
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
            raise ValueError(f"Merge request !{mr_iid} not found: {e}")

        # Get merge request diffs with pagination
        try:
            kwargs = {
                "page": page,
                "per_page": per_page,
            }
            diffs_list = mr.diffs.list(**kwargs)
        except Exception as e:
            raise ValueError(f"Failed to get diffs for merge request !{mr_iid}: {e}")

        # Serialize diffs
        diffs = []
        for diff_item in diffs_list:
            diff_data = {
                "old_path": getattr(diff_item, "old_path", None),
                "new_path": getattr(diff_item, "new_path", None),
                "a_mode": getattr(diff_item, "a_mode", None),
                "b_mode": getattr(diff_item, "b_mode", None),
                "new_file": getattr(diff_item, "new_file", False),
                "renamed_file": getattr(diff_item, "renamed_file", False),
                "deleted_file": getattr(diff_item, "deleted_file", False),
                "diff": getattr(diff_item, "diff", ""),
            }
            diffs.append(diff_data)

        return {
            "mr_iid": mr_iid,
            "diffs": diffs,
            "total_results": len(diffs),
        }

    return await asyncio.to_thread(_sync_list_merge_request_diffs)
